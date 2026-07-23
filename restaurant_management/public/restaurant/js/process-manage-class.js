ProcessManage = class ProcessManage {
    constructor(options) {
        Object.assign(this, options);
        this.status = "close";
        this.modal = null;
        this.active_view = "commands";
        this.command_service_filter = "all";
        this.dashboard = null;
        this.command_snapshot_initialized = false;
        this.seen_command_keys = new Set();
        this.loading = false;
        this.transitioning = false;
        this.pending_reload = false;
        this.stale = true;
        this.reload_timeout = null;
        this.reconciliation_interval = null;
        this.request_serial = 0;
        this.fullscreen_change_handler = () => this.update_fullscreen_button();

        this.initialize();
        this.init_realtime();
    }

    initialize() {
        this.title = this.table.room.data.description + " (" + this.table.data.description + ")";
        this.modal = RMHelper.default_full_modal(this.title, () => this.make());
        this.modal.modal.$wrapper.addClass("production-center-modal");
        document.addEventListener("fullscreenchange", this.fullscreen_change_handler);
        this.modal.modal.$wrapper
            .on("hidden.bs.modal.production-center", () => {
                this.status = "close";
                this.stop_reconciliation();
                this.exit_fullscreen();
                document.removeEventListener("fullscreenchange", this.fullscreen_change_handler);
            })
            .on("shown.bs.modal.production-center", () => {
                this.status = "open";
                document.addEventListener("fullscreenchange", this.fullscreen_change_handler);
                this.update_fullscreen_button();
                this.start_reconciliation();
                if (this.stale) this.schedule_reload();
            });
    }

    init_realtime() {
        frappe.realtime.on("production_center_update", data => {
            if (data && data.center === this.table.data.name) this.schedule_reload();
        });
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden && this.is_open() && this.stale) this.schedule_reload();
        });
    }

    make() {
        this.status = "open";
        this.make_dom();
        this.start_reconciliation();
        this.reload();
    }

    show() {
        this.status = "open";
        this.modal.show();
        this.start_reconciliation();
        this.reload();
    }

    close() {
        this.status = "close";
        this.stop_reconciliation();
        this.exit_fullscreen();
        this.modal.hide();
    }

    fullscreen_element() {
        return this.modal && this.modal.modal.$wrapper.get(0);
    }

    is_fullscreen() {
        return document.fullscreenElement === this.fullscreen_element();
    }

    toggle_fullscreen() {
        if (this.is_fullscreen()) {
            this.exit_fullscreen();
            return;
        }

        const element = this.fullscreen_element();
        if (!element || !element.requestFullscreen) {
            frappe.show_alert({
                message: __("Full screen is not supported by this browser"),
                indicator: "orange"
            });
            return;
        }

        element.requestFullscreen().catch(() => {
            frappe.show_alert({
                message: __("Could not enter full screen"),
                indicator: "red"
            });
        });
    }

    exit_fullscreen() {
        if (this.is_fullscreen() && document.exitFullscreen) {
            document.exitFullscreen().catch(() => {});
        }
    }

    update_fullscreen_button() {
        if (!this.modal) return;
        const active = this.is_fullscreen();
        this.modal.modal.$wrapper.find(".production-center-fullscreen")
            .toggleClass("active", active)
            .attr("aria-pressed", active ? "true" : "false")
            .empty()
            .append(
                $("<span>", { class: `fa ${active ? "fa-compress" : "fa-expand"}` }),
                " ",
                active ? __("Exit full screen") : __("Full screen")
            );
    }

    is_open() {
        return this.status === "open";
    }

    make_dom() {
        const back_button = RMHelper.return_main_button(this.title, () => this.close());
        const refresh_button = $("<button>", {
            type: "button",
            class: "btn btn-default btn-flat production-center-refresh"
        }).append($("<span>", { class: "fa fa-refresh" }), " ", __("Refresh"));
        const fullscreen_button = $("<button>", {
            type: "button",
            class: "btn btn-default btn-flat production-center-fullscreen",
            title: __("Full screen"),
            "aria-pressed": "false"
        }).append($("<span>", { class: "fa fa-expand" }), " ", __("Full screen"));

        this.modal.title_container.empty().append(back_button.html(), refresh_button);
        this.modal.buttons_container.find(".production-center-fullscreen").remove();
        this.modal.buttons_container.prepend(fullscreen_button);
        this.modal.container.empty().append(this.template());

        this.modal.container
            .off("click.production-center")
            .on("click.production-center", "[data-production-view]", event => {
                this.set_active_view($(event.currentTarget).data("production-view"));
            })
            .on("click.production-center", "[data-command-service-filter]", event => {
                this.set_command_service_filter($(event.currentTarget).data("command-service-filter"));
            })
            .on("click.production-center", ".production-center-refresh", () => this.reload())
            .on("click.production-center", ".production-command-action", event => {
                const key = $(event.currentTarget).data("command-key");
                const command = (this.dashboard && this.dashboard.commands || [])
                    .find(row => row.key === key);
                const action = command && command.bulk_action;
                if (command && action) {
                    this.transition_items(
                        command,
                        action.identifiers,
                        false,
                        action.expected_status,
                        action.partial
                    );
                }
            })
            .on("click.production-center", ".production-item-action", event => {
                const key = $(event.currentTarget).data("command-key");
                const identifier = $(event.currentTarget).data("item-identifier");
                const command = (this.dashboard && this.dashboard.commands || [])
                    .find(row => row.key === key);
                const item = command && (command.items || []).find(row => row.identifier === identifier);
                if (command && item) this.transition_items(command, [identifier], true, item.status);
            })
            .on("click.production-center", ".production-timing-button", event => {
                const key = $(event.currentTarget).data("command-key");
                const identifier = $(event.currentTarget).data("item-identifier");
                const command = [
                    ...((this.dashboard && this.dashboard.commands) || []),
                    ...((this.dashboard && this.dashboard.attended) || [])
                ].find(row => row.key === key);
                const item = command && (command.items || []).find(row => row.identifier === identifier);
                if (item) this.show_item_timing(item);
            })
            .on("click.production-center", ".production-consolidation-timing", event => {
                const item_code = $(event.currentTarget).data("item-code");
                const row = ((this.dashboard && this.dashboard.consolidation) || [])
                    .find(item => item.item_code === item_code);
                if (row) this.show_consolidation_timing(row);
            });

        refresh_button.on("click", () => this.reload());
        fullscreen_button.on("click", () => this.toggle_fullscreen());
        this.update_active_tab();
    }

    template() {
        return `
            <div class="production-center-shell">
                <div class="production-center-tabs" role="tablist">
                    <button type="button" class="btn btn-default" data-production-view="consolidation">
                        <span class="fa fa-list"></span>
                        <span>${__("Dish consolidation")}</span>
                        <span class="production-center-count" data-count="consolidation">0</span>
                    </button>
                    <button type="button" class="btn btn-default" data-production-view="commands">
                        <span class="fa fa-ticket"></span>
                        <span>${__("Commands")}</span>
                        <span class="production-center-count" data-count="commands">0</span>
                    </button>
                    <button type="button" class="btn btn-default" data-production-view="attended">
                        <span class="fa fa-check-circle"></span>
                        <span>${__("Attended orders")}</span>
                        <span class="production-center-count" data-count="attended">0</span>
                    </button>
                </div>
                <div class="production-command-filter" role="group" aria-label="${__("Order source")}">
                    <span class="production-command-filter-label">${__("Order source")}</span>
                    <div class="production-command-filter-options">
                        ${this.command_filter_button("all", "All")}
                        ${this.command_filter_button("tables", "Tables")}
                        ${this.command_filter_button("delivery", "Delivery")}
                        ${this.command_filter_button("pickup", "Pickup")}
                    </div>
                </div>
                <div class="production-center-summary"></div>
                <div class="production-center-content" aria-live="polite"></div>
            </div>`;
    }

    root() {
        return this.modal.container.find(".production-center-shell");
    }

    set_active_view(view) {
        if (!["commands", "consolidation", "attended"].includes(view)) return;
        this.active_view = view;
        this.update_active_tab();
        this.update_command_filter();
        this.render_active_view();
    }

    command_filter_button(value, label) {
        return `
            <button type="button" class="btn btn-default" data-command-service-filter="${value}" aria-pressed="false">
                <span>${__(label)}</span>
                <span class="production-command-filter-count" data-command-service-count="${value}">0</span>
            </button>`;
    }

    set_command_service_filter(filter) {
        if (!["all", "tables", "delivery", "pickup"].includes(filter)) return;
        this.command_service_filter = filter;
        this.update_command_filter();
        this.render_active_view();
    }

    update_command_filter() {
        const root = this.root();
        root.find(".production-command-filter").toggle(this.active_view === "commands");
        root.find("[data-command-service-filter]").each((index, element) => {
            const active = $(element).data("command-service-filter") === this.command_service_filter;
            $(element)
                .toggleClass("active", active)
                .attr("aria-pressed", active ? "true" : "false");
        });
    }

    command_service_group(command) {
        const service_type = String(command && command.service_type || "").trim().toLowerCase();
        if (service_type === "delivery") return "delivery";
        if (service_type === "pickup") return "pickup";
        return "tables";
    }

    filtered_commands() {
        const commands = (this.dashboard && this.dashboard.commands) || [];
        if (this.command_service_filter === "all") return commands;
        return commands.filter(command => this.command_service_group(command) === this.command_service_filter);
    }

    update_command_filter_counts() {
        const commands = (this.dashboard && this.dashboard.commands) || [];
        const counts = { all: commands.length, tables: 0, delivery: 0, pickup: 0 };
        commands.forEach(command => {
            counts[this.command_service_group(command)] += 1;
        });
        Object.entries(counts).forEach(([key, value]) => {
            this.root().find(`[data-command-service-count="${key}"]`).text(value);
        });
    }

    update_active_tab() {
        const root = this.root();
        root.find("[data-production-view]").each((index, element) => {
            const active = $(element).data("production-view") === this.active_view;
            $(element)
                .toggleClass("active", active)
                .attr("aria-selected", active ? "true" : "false");
        });
    }

    reload() {
        if (!this.is_open() || document.hidden) {
            this.stale = true;
            return;
        }
        if (this.loading) {
            this.pending_reload = true;
            return;
        }

        this.loading = true;
        this.pending_reload = false;
        const serial = ++this.request_serial;
        this.show_loading();

        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "production_center_dashboard",
            args: {},
            always: response => {
                if (serial !== this.request_serial) return;
                this.loading = false;

                if (response && !response.exc && response.message) {
                    this.notify_new_commands(response.message);
                    this.dashboard = response.message;
                    this.stale = false;
                    this.render_dashboard();
                } else if (!this.dashboard) {
                    this.show_error();
                }

                if (this.pending_reload) {
                    this.pending_reload = false;
                    this.reload();
                }
            }
        });
    }

    schedule_reload() {
        this.stale = true;
        clearTimeout(this.reload_timeout);
        if (!this.is_open() || document.hidden) return;
        this.reload_timeout = setTimeout(() => {
            this.reload();
        }, 150);
    }

    start_reconciliation() {
        if (this.reconciliation_interval) return;
        this.reconciliation_interval = setInterval(() => {
            if (this.is_open() && !document.hidden) this.reload();
        }, 5000);
    }

    stop_reconciliation() {
        if (this.reconciliation_interval) {
            clearInterval(this.reconciliation_interval);
            this.reconciliation_interval = null;
        }
    }

    show_loading() {
        if (this.dashboard) return;
        this.root().find(".production-center-content").empty().append(
            $("<div>", { class: "production-center-state" })
                .append($("<span>", { class: "fa fa-spinner fa-spin" }), " ", __("Loading production center"))
        );
    }

    show_error() {
        this.root().find(".production-center-content").empty().append(
            $("<div>", { class: "production-center-state text-danger" })
                .text(__("Production center data could not be loaded"))
        );
    }

    notify_new_commands(dashboard) {
        const keys = (dashboard && dashboard.commands || [])
            .map(command => command.key)
            .filter(Boolean);

        if (!this.command_snapshot_initialized) {
            keys.forEach(key => this.seen_command_keys.add(key));
            this.command_snapshot_initialized = true;
            return 0;
        }

        const new_keys = keys.filter(key => !this.seen_command_keys.has(key));
        keys.forEach(key => this.seen_command_keys.add(key));
        if (
            !new_keys.length
            || !this.is_open()
            || document.hidden
            || this.active_view !== "commands"
        ) {
            return 0;
        }

        frappe.utils.play_sound("chime");
        frappe.show_alert({
            message: new_keys.length === 1
                ? __("New command received")
                : __("{0} new commands received", [new_keys.length]),
            indicator: "orange"
        });
        return new_keys.length;
    }

    render_dashboard() {
        const counts = this.dashboard.counts || {};
        const root = this.root();
        root.find('[data-count="consolidation"]').text(this.format_qty(counts.daily_qty || 0));
        root.find('[data-count="commands"]').text(counts.commands || 0);
        root.find('[data-count="attended"]').text(this.format_qty(counts.attended_qty || 0));

        this.table.data.orders_count = counts.active_items || 0;
        this.table.set_orders_count();

        const summary = root.find(".production-center-summary").empty();
        summary.append(
            $("<span>").text(__("Dishes today: {0}", [this.format_qty(counts.daily_qty || 0)])),
            $("<span>").text(__("Active dishes: {0}", [this.format_qty(counts.active_qty || 0)])),
            $("<span>").text(__("Prepared today: {0}", [this.format_qty(counts.completed_qty || 0)])),
            $("<span>").text(__("Commands: {0}", [counts.commands || 0]))
        );

        this.update_command_filter_counts();
        this.update_command_filter();
        this.render_active_view();
    }

    render_active_view() {
        if (!this.dashboard) return;
        const content = this.root().find(".production-center-content").empty();

        if (this.active_view === "consolidation") {
            this.render_consolidation(content);
        } else if (this.active_view === "attended") {
            this.render_commands(content, this.dashboard.attended || [], true);
        } else {
            this.render_commands(content, this.filtered_commands(), false, this.command_service_filter !== "all");
        }

        const truncated = this.dashboard.truncated || {};
        if (
            (this.active_view === "attended" && truncated.attended) ||
            (this.active_view !== "attended" && truncated.active)
        ) {
            content.prepend(
                $("div", { class: "alert alert-warning production-center-limit" })
                    .text(__("Only the most recent production records are shown"))
            );
        }
    }

    render_consolidation(content) {
        const rows = this.dashboard.consolidation || [];
        if (!rows.length) {
            this.render_empty(content, __("There are no dishes today"));
            return;
        }

        const table = $("<table>", { class: "table table-bordered production-consolidation-table" });
        const header = $("<tr>")
            .append($("<th>").text(__("Dish")))
            .append($("<th>", { class: "text-center" }).text(__("Pending")))
            .append($("<th>", { class: "text-center" }).text(__("In preparation")))
            .append($("<th>", { class: "text-center" }).text(__("Prepared")))
            .append($("<th>", { class: "text-center" }).text(__("Total today")))
            .append($("<th>", { class: "text-center" }).text(__("Average time")));
        table.append($("<thead>").append(header));

        const body = $("<tbody>");
        rows.forEach(row => {
            body.append(
                $("<tr>")
                    .append($("<td>").append(
                        $("<strong>").text(row.item_name || row.item_code),
                        row.item_name && row.item_name !== row.item_code
                            ? $("<small>").text(row.item_code)
                            : null
                    ))
                    .append($("<td>", { class: "text-center production-qty pending" }).text(this.format_qty(row.pending_qty)))
                    .append($("<td>", { class: "text-center production-qty processing" }).text(this.format_qty(row.processing_qty)))
                    .append($("<td>", { class: "text-center production-qty completed" }).text(this.format_qty(row.completed_qty)))
                    .append($("<td>", { class: "text-center production-qty total" }).text(this.format_qty(row.total_qty)))
                    .append($("<td>", { class: "text-center" }).append(this.consolidation_timing_button(row)))
            );
        });
        table.append(body);
        content.append($("<div>", { class: "table-responsive" }).append(table));
    }

    render_commands(content, commands, attended, filtered = false) {
        if (!commands.length) {
            this.render_empty(
                content,
                attended
                    ? __("There are no attended orders today")
                    : filtered
                        ? __("There are no active commands for the selected source")
                        : __("There are no active commands")
            );
            return;
        }

        const grid = $("<div>", { class: "production-command-grid" });
        commands.forEach(command => grid.append(this.command_card(command, attended)));
        content.append(grid);
    }

    command_card(command, attended) {
        const card = $("<article>", { class: "production-command-card" });
        const header = $("<header>", { class: "production-command-header" });
        const title = $("<div>").append(
            $("<strong>").text(command.short_name || command.order_name),
            $("<span>").text(command.table_description || __("No table"))
        );
        const elapsed = $("<span>", { class: "production-command-time" })
            .text(RMHelper.prettyDate(command.ordered_time, true));
        header.append(title, elapsed);
        card.append(header);

        const meta = $("<div>", { class: "production-command-meta" });
        if (command.waiter) meta.append($("<span>").text(__("Waiter: {0}", [command.waiter])));
        meta.append($("<span>").text(__("Status: {0}", [this.status_label(command.status)])));
        card.append(meta);

        if (command.comment) {
            card.append($("<div>", { class: "production-command-comment" }).text(command.comment));
        }

        const item_list = $("<div>", { class: "production-command-items" });
        (command.items || []).forEach(item => {
            const description = $("<span>", { class: "production-command-item-name" }).append(
                $("<span>").text(item.item_name || item.item_code),
                $("<small>", { class: "production-item-status" })
                    .text(__("Status: {0}", [this.status_label(item.status)])),
                this.item_timing_button(command, item)
            );
            const row = $("<div>", { class: "production-command-item" }).append(
                $("<strong>", { class: "production-command-item-qty" }).text(`[${this.format_qty(item.qty)}]`),
                description
            );
            if (!attended && this.dashboard.can_transition && item.next_status) {
                row.append(
                    $("<button>", {
                        type: "button",
                        class: "btn btn-xs btn-default production-item-action"
                    })
                        .data("command-key", command.key)
                        .data("item-identifier", item.identifier)
                        .text(this.action_label(item.next_status, true))
                );
            }
            if (item.notes) row.append($("<small>", { class: "production-command-note" }).text(item.notes));
            item_list.append(row);
        });
        card.append(item_list);

        const footer = $("<footer>", { class: "production-command-footer" }).append(
            $("<span>").text(__("Dishes: {0}", [this.format_qty(command.qty || 0)]))
        );
        const bulk_action = command.bulk_action;
        if (
            !attended &&
            this.dashboard.can_transition &&
            bulk_action &&
            (bulk_action.partial || bulk_action.identifiers.length > 1)
        ) {
            footer.append(
                $("<button>", {
                    type: "button",
                    class: "btn btn-primary production-command-action"
                })
                    .data("command-key", command.key)
                    .text(
                        bulk_action.partial
                            ? this.pending_action_label(bulk_action.next_status)
                            : this.action_label(bulk_action.next_status, false)
                    )
            );
        }
        card.append(footer);
        return card;
    }

    transition_items(
        command,
        identifiers,
        single_item,
        expected_status = command.status,
        partial = false
    ) {
        if (this.transitioning || !identifiers || !identifiers.length) return;
        this.transitioning = true;
        this.root().find(".production-command-action, .production-item-action").prop("disabled", true);
        RM.working(
            single_item
                ? __("Updating dish")
                : partial ? __("Updating pending dishes") : __("Updating command"),
            false
        );
        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "set_commands_status",
            args: {
                identifiers: identifiers,
                expected_status: expected_status
            },
            always: response => {
                this.transitioning = false;
                RM.ready();
                if (response && !response.exc && response.message) {
                    frappe.show_alert({
                        message: single_item
                            ? __("Dish updated to {0}", [this.status_label(response.message.status)])
                            : partial
                                ? __("Pending dishes updated to {0}", [this.status_label(response.message.status)])
                                : __("Command updated to {0}", [this.status_label(response.message.status)]),
                        indicator: "green"
                    });
                }
                this.root().find(".production-command-action, .production-item-action").prop("disabled", false);
                this.stale = true;
                this.reload();
            }
        });
    }

    render_empty(content, message) {
        content.append(
            $("<div>", { class: "production-center-state" }).append(
                $("<span>", { class: "fa fa-cutlery" }),
                $("<p>").text(message)
            )
        );
    }

    action_label(next_status, single_item) {
        const command_labels = {
            Processing: __("Start entire command"),
            Completed: __("Complete entire command"),
            Delivering: __("Deliver entire command"),
            Delivered: __("Mark command as delivered")
        };
        const item_labels = {
            Processing: __("Start dish"),
            Completed: __("Complete dish"),
            Delivering: __("Deliver dish"),
            Delivered: __("Mark dish as delivered")
        };
        return (single_item ? item_labels : command_labels)[next_status] || __("Advance");
    }

    pending_action_label(next_status) {
        return {
            Processing: __("Start pending dishes"),
            Completed: __("Complete pending dishes"),
            Delivering: __("Deliver pending dishes"),
            Delivered: __("Mark pending dishes as delivered")
        }[next_status] || __("Advance pending dishes");
    }

    item_timing_button(command, item) {
        const timing = item.timing || {};
        return $("<button>", {
            type: "button",
            class: `production-timing-button production-timing-${timing.status || "no_target"}`,
            title: __("View time details")
        })
            .data("command-key", command.key)
            .data("item-identifier", item.identifier)
            .text(this.item_timing_label(item.status, timing));
    }

    item_timing_label(status, timing) {
        if (
            status === "Sent" &&
            timing.waiting_minutes !== null &&
            typeof timing.waiting_minutes !== "undefined"
        ) {
            return __("Wait {0} min", [this.format_minutes(timing.waiting_minutes)]);
        }
        if (timing.preparation_minutes !== null && typeof timing.preparation_minutes !== "undefined") {
            if (Number(timing.target_minutes || 0) > 0) {
                return __("Prep. {0}/{1} min", [
                    this.format_minutes(timing.preparation_minutes),
                    this.format_minutes(timing.target_minutes)
                ]);
            }
            return __("Prep. {0} min", [this.format_minutes(timing.preparation_minutes)]);
        }
        if (Number(timing.target_minutes || 0) > 0) {
            return __("Target {0} min", [this.format_minutes(timing.target_minutes)]);
        }
        return __("No target");
    }

    consolidation_timing_button(row) {
        const actual = row.average_preparation_minutes;
        const target = row.average_target_minutes;
        let label = __("No timing data");
        if (actual !== null && typeof actual !== "undefined" && Number(target || 0) > 0) {
            label = __("Prep. {0} / Target {1} min", [
                this.format_minutes(actual),
                this.format_minutes(target)
            ]);
        } else if (actual !== null && typeof actual !== "undefined") {
            label = __("Prep. {0} min", [this.format_minutes(actual)]);
        } else if (Number(target || 0) > 0) {
            label = __("Target {0} min", [this.format_minutes(target)]);
        }
        return $("<button>", {
            type: "button",
            class: `production-consolidation-timing production-timing-${row.timing_status || "no_target"}`,
            title: __("View time details")
        }).data("item-code", row.item_code).text(label);
    }

    show_item_timing(item) {
        const timing = item.timing || {};
        this.show_timing_detail(
            item.item_name || item.item_code,
            timing,
            timing.target_source
        );
    }

    show_consolidation_timing(row) {
        this.show_timing_detail(
            __("Daily average: {0}", [row.item_name || row.item_code]),
            {
                waiting_minutes: row.average_waiting_minutes,
                preparation_minutes: row.average_preparation_minutes,
                total_minutes: row.average_total_minutes,
                target_minutes: row.average_target_minutes,
                variance_minutes: (
                    row.average_preparation_minutes !== null && Number(row.average_target_minutes || 0) > 0
                        ? Number(row.average_preparation_minutes) - Number(row.average_target_minutes)
                        : null
                ),
                status: row.timing_status
            },
            row.target_source
        );
    }

    show_timing_detail(title, timing, target_source) {
        const detail = $("<div>", { class: "production-timing-detail" });
        const rows = [];
        if (timing.ordered_at || timing.processing_started_at || timing.completed_at) {
            rows.push(
                [__("Ordered at"), this.datetime_or_dash(timing.ordered_at)],
                [__("Processing started at"), this.datetime_or_dash(timing.processing_started_at)],
                [__("Processing started by"), timing.processing_started_by || "—"],
                [__("Completed at"), this.datetime_or_dash(timing.completed_at)],
                [__("Completed by"), timing.completed_by || "—"]
            );
        }
        rows.push(
            [__("Waiting time"), this.minutes_or_dash(timing.waiting_minutes)],
            [__("Preparation time"), this.minutes_or_dash(timing.preparation_minutes)],
            [__("Total time"), this.minutes_or_dash(timing.total_minutes)],
            [__("Preparation target"), this.minutes_or_dash(timing.target_minutes)],
            [__("Difference from target"), this.variance_or_dash(timing.variance_minutes)],
            [__("Target source"), this.target_source_label(target_source)],
            [__("Performance"), this.performance_label(timing.status)]
        );
        rows.forEach(([label, value]) => {
            detail.append(
                $("<div>", { class: "production-timing-detail-row" }).append(
                    $("<span>").text(label),
                    $("<strong>").text(value)
                )
            );
        });
        frappe.msgprint({
            title: title,
            message: detail.prop("outerHTML"),
            indicator: this.performance_indicator(timing.status)
        });
    }

    target_source_label(target_source) {
        if (target_source === "Item") return __("Product");
        if (target_source === "Item Group") return __("Product Group");
        return target_source ? __(target_source) : __("No target");
    }

    minutes_or_dash(value) {
        return value === null || typeof value === "undefined"
            ? "—"
            : __("{0} min", [this.format_minutes(value)]);
    }

    datetime_or_dash(value) {
        return value ? frappe.datetime.str_to_user(value) : "—";
    }

    variance_or_dash(value) {
        if (value === null || typeof value === "undefined") return "—";
        const number = Number(value || 0);
        const prefix = number > 0 ? "+" : "";
        return `${prefix}${this.format_minutes(number)} min`;
    }

    performance_label(status) {
        return {
            on_time: __("On time"),
            warning: __("Near target"),
            late: __("Over target"),
            no_target: __("No target")
        }[status] || __("No target");
    }

    performance_indicator(status) {
        return {
            on_time: "green",
            warning: "orange",
            late: "red"
        }[status] || "blue";
    }

    status_label(status) {
        return {
            Sent: __("Pending"),
            Processing: __("In preparation"),
            Completed: __("Attended"),
            Delivering: __("Delivering"),
            Delivered: __("Delivered"),
            Mixed: __("Mixed")
        }[status] || status;
    }

    format_qty(value) {
        const number = Number(value || 0);
        return Number.isInteger(number) ? number : number.toFixed(2);
    }

    format_minutes(value) {
        const number = Number(value || 0);
        return Number.isInteger(number) ? number : number.toFixed(1);
    }

    // Realtime compatibility: every relevant item event reconciles the active view
    // against persisted center-scoped data instead of mutating one popup in memory.
    get_commands_food() {
        this.reload();
    }

    make_food_commands() {
        this.schedule_reload();
    }

    check_items() {
        this.schedule_reload();
    }

    remove_item() {
        this.schedule_reload();
    }

    sync_orders_count() {
        if (!this.dashboard) return;
        this.table.data.orders_count = this.dashboard.counts.active_items || 0;
        this.table.set_orders_count();
    }

    command_container() {
        return this.root().find(".production-center-content").get(0);
    }
}
