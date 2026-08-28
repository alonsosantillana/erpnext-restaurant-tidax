frappe.pages["restaurant-print-console"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Restaurant Print Station"),
        single_column: true,
    });
    page.main.html(`<div data-role="station-loading" class="text-muted">${__("Cargando estación de impresión...")}</div>`);
};

frappe.pages["restaurant-print-console"].on_page_show = async function(wrapper) {
    try {
        const controller = await get_restaurant_print_station_controller(wrapper);
        await controller.start();
    } catch (error) {
        render_restaurant_print_station_error(wrapper, error);
    }
};

frappe.pages["restaurant-print-console"].on_page_hide = function(wrapper) {
    if (wrapper.page.station_controller) wrapper.page.station_controller.stop();
};

async function get_restaurant_print_station_controller(wrapper) {
    if (wrapper.page.station_controller) return wrapper.page.station_controller;

    if (!frappe.silent_print || !frappe.silent_print.WebSocketPrinter) {
        await frappe.require("/assets/silent_print/js/silent_print_v15.js");
    }
    if (!frappe.silent_print || !frappe.silent_print.WebSocketPrinter) {
        throw new Error(__("No se pudo cargar el cliente de Silent Print."));
    }

    wrapper.page.main.find('[data-role="station-loading"]').remove();
    wrapper.page.station_controller = new RestaurantPrintStationPage(wrapper.page);
    return wrapper.page.station_controller;
}

function render_restaurant_print_station_error(wrapper, error) {
    const message = error?.message || error?.exc || String(error || __("Error desconocido"));
    console.error("Restaurant Print Station could not start", error);
    wrapper.page.main.html(`
        <div class="alert alert-danger">
            <strong>${__("No se pudo iniciar la estación de impresión")}</strong><br>
            ${frappe.utils.escape_html(message)}
        </div>`);
}

class RestaurantPrintStationPage {
    constructor(page) {
        this.page = page;
        this.client_id = sessionStorage.getItem("restaurant_print_station_client")
            || frappe.silent_print.make_id();
        sessionStorage.setItem("restaurant_print_station_client", this.client_id);
        this.running = false;
        this.processing = false;
        this.station = null;
        this.$root = $('<div class="restaurant-print-station"></div>').appendTo(page.main);
        this.printer = new frappe.silent_print.WebSocketPrinter({
            keep_alive: true,
            max_queue: 5,
            on_state_change: state => this.render_state(state),
        });
        this.page.set_primary_action(__("Reconnect"), () => this.printer.reconnect(), "refresh");
        this.render_shell();
    }

    render_shell() {
        this.$root.html(`
            <div class="station-summary">
                <div class="station-card"><span>${__("Station")}</span><strong data-role="station">—</strong></div>
                <div class="station-card"><span>${__("Hardware Bridge")}</span><strong data-role="bridge" class="state-closed">${__("Disconnected")}</strong></div>
                <div class="station-card"><span>${__("Pending")}</span><strong data-role="pending">0</strong></div>
                <div class="station-card"><span>${__("Attention required")}</span><strong data-role="attention">0</strong></div>
            </div>
            <div class="frappe-card">
                <table><thead><tr>
                    <th>${__("Job")}</th><th>${__("Type")}</th><th>${__("Document")}</th>
                    <th>${__("Status")}</th><th>${__("Attempts")}</th><th>${__("Details")}</th><th>${__("Action")}</th>
                </tr></thead><tbody data-role="jobs"></tbody></table>
            </div>`);
    }

    async start() {
        if (this.running) return;
        this.running = true;
        try {
            const response = await frappe.call({method: "restaurant_management.printing.get_station_bootstrap", type: "GET"});
            const stations = response.message.stations || [];
            if (!stations.length) {
                this.$root.prepend(`<div class="alert alert-warning">${__("No enabled print station is assigned to this user and company.")}</div>`);
                this.running = false;
                return;
            }
            this.station = stations[0];
            this.$root.find('[data-role="station"]').text(this.station.station_name);
            this.printer.options.url = `${response.message.bridge_url}/printer`;
            this.printer.connect();
            await this.heartbeat();
            await this.refresh_jobs();
            this.heartbeat_timer = setInterval(() => this.heartbeat(), 15000);
            this.poll_timer = setInterval(() => this.poll(), 3000);
            frappe.realtime.on("restaurant_print_job", this.realtime_handler = event => {
                if (event.station === this.station.name) this.poll();
            });
            this.poll();
        } catch (error) {
            this.running = false;
            throw error;
        }
    }

    stop() {
        this.running = false;
        clearInterval(this.heartbeat_timer);
        clearInterval(this.poll_timer);
        if (this.realtime_handler) frappe.realtime.off("restaurant_print_job", this.realtime_handler);
        this.printer.close();
    }

    render_state(state) {
        const label = state === "open" ? __("Connected") : __(state);
        this.$root.find('[data-role="bridge"]')
            .removeClass("state-open state-connecting state-closed state-failed")
            .addClass(`state-${state}`).text(label);
    }

    heartbeat() {
        if (!this.station || !this.running) return Promise.resolve();
        return frappe.call({
            method: "restaurant_management.printing.heartbeat",
            type: "POST",
            args: {
                station: this.station.name,
                client_id: this.client_id,
                hw_bridge_version: "0.13.0",
                bridge_state: this.printer.getState(),
            },
        });
    }

    async poll() {
        if (!this.running || this.processing || !this.station) return;
        if (!this.printer.isConnected()) {
            await this.refresh_jobs();
            return;
        }
        this.processing = true;
        try {
            await this.heartbeat();
            const response = await frappe.call({
                method: "restaurant_management.printing.claim_jobs",
                type: "POST",
                args: {station: this.station.name, client_id: this.client_id, limit: 1},
            });
            for (const job of response.message || []) await this.process_job(job);
            await this.refresh_jobs();
        } finally {
            this.processing = false;
        }
    }

    async process_job(job) {
        try {
            const rendered = await frappe.call({
                method: "restaurant_management.printing.render_job",
                type: "POST", args: {job, client_id: this.client_id},
            });
            const result = await this.printer.submit(rendered.message);
            await this.acknowledge(job, {success: 1, printer: result.printer, message: result.message});
        } catch (error) {
            const details = error || {};
            if (details.ambiguous || details.sent) {
                await this.acknowledge(job, {
                    success: 0,
                    ambiguous: details.ambiguous ? 1 : 0,
                    printer: details.printer,
                    message: details.message || String(details),
                });
            } else {
                await frappe.call({
                    method: "restaurant_management.printing.release_job",
                    type: "POST", args: {job, client_id: this.client_id, message: details.message || String(details)},
                });
            }
        }
    }

    acknowledge(job, values) {
        return frappe.call({
            method: "restaurant_management.printing.acknowledge_job",
            type: "POST", args: Object.assign({job, client_id: this.client_id}, values),
        });
    }

    async refresh_jobs() {
        if (!this.station) return;
        const response = await frappe.call({
            method: "restaurant_management.printing.station_jobs",
            type: "GET",
            args: {station: this.station.name, limit: 30},
        });
        const jobs = response.message || [];
        this.$root.find('[data-role="pending"]').text(jobs.filter(j => ["Pending", "Sending"].includes(j.status)).length);
        this.$root.find('[data-role="attention"]').text(jobs.filter(j => ["Failed", "Ambiguous"].includes(j.status)).length);
        const is_admin = frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("resto_admin");
        const is_cashier = frappe.user_roles.includes("resto_cajero");
        this.$root.find("[data-role=jobs]").html(jobs.map(job => `<tr>
            <td>${frappe.utils.escape_html(job.name)}</td>
            <td>${frappe.utils.escape_html(job.route_type)}</td>
            <td>${frappe.utils.escape_html(job.source_name)}</td>
            <td>${frappe.utils.escape_html(job.status)}</td>
            <td>${job.attempt_count || 0}</td>
            <td class="job-error">${frappe.utils.escape_html(job.last_error || job.printer_name || "")}</td>
            <td>${((job.status === "Failed" && (is_admin || is_cashier))
                    || (job.status === "Ambiguous" && is_admin))
                ? `<button class="btn btn-xs btn-default" data-retry-job="${frappe.utils.escape_html(job.name)}">${__("Retry")}</button>`
                : ""}</td>
        </tr>`).join(""));
        this.$root.find("[data-retry-job]").on("click", event => {
            frappe.call({
                method: "restaurant_management.printing.retry_job",
                type: "POST",
                args: {job: $(event.currentTarget).attr("data-retry-job")},
                callback: () => this.poll(),
            });
        });
    }
}
