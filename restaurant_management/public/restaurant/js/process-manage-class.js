ProcessManage = class ProcessManage {
    constructor(options) {
        Object.assign(this, options);
        this.status = "close";
        this.modal = null;
        this.active_view = "commands";
        this.dashboard = null;
        this.loading = false;
        this.transitioning = false;
        this.pending_reload = false;
        this.stale = true;
        this.reload_timeout = null;
        this.reconciliation_interval = null;
        this.request_serial = 0;

        this.initialize();
        this.init_realtime();
    }

    initialize() {
        this.title = this.table.room.data.description + " (" + this.table.data.description + ")";
        this.modal = RMHelper.default_full_modal(this.title, () => this.make());
        this.modal.modal.$wrapper
            .on("hidden.bs.modal.production-center", () => {
                this.status = "close";
                this.stop_reconciliation();
            })
            .on("shown.bs.modal.production-center", () => {
                this.status = "open";
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
        this.modal.hide();
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

        this.modal.title_container.empty().append(back_button.html(), refresh_button);
        this.modal.container.empty().append(this.template());

        this.modal.container
            .off("click.production-center")
            .on("click.production-center", "[data-production-view]", event => {
                this.set_active_view($(event.currentTarget).data("production-view"));
            })
            .on("click.production-center", ".production-center-refresh", () => this.reload())
            .on("click.production-center", ".production-command-action", event => {
                const key = $(event.currentTarget).data("command-key");
                const command = (this.dashboard && this.dashboard.commands || [])
                    .find(row => row.key === key);
                if (command) this.transition_items(command, command.identifiers, false);
            })
            .on("click.production-center", ".production-item-action", event => {
                const key = $(event.currentTarget).data("command-key");
                const identifier = $(event.currentTarget).data("item-identifier");
                const command = (this.dashboard && this.dashboard.commands || [])
                    .find(row => row.key === key);
                if (command && identifier) this.transition_items(command, [identifier], true);
            });

        refresh_button.on("click", () => this.reload());
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
        this.render_active_view();
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

    render_dashboard() {
        const counts = this.dashboard.counts || {};
        const root = this.root();
        root.find('[data-count="consolidation"]').text(this.format_qty(counts.active_qty || 0));
        root.find('[data-count="commands"]').text(counts.commands || 0);
        root.find('[data-count="attended"]').text(this.format_qty(counts.attended_qty || 0));

        this.table.data.orders_count = counts.active_items || 0;
        this.table.set_orders_count();

        const summary = root.find(".production-center-summary").empty();
        summary.append(
            $("<span>").text(__("Active dishes: {0}", [this.format_qty(counts.active_qty || 0)])),
            $("<span>").text(__("Commands: {0}", [counts.commands || 0]))
        );

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
            this.render_commands(content, this.dashboard.commands || [], false);
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
            this.render_empty(content, __("There are no active dishes"));
            return;
        }

        const table = $("<table>", { class: "table table-bordered production-consolidation-table" });
        const header = $("<tr>")
            .append($("<th>").text(__("Dish")))
            .append($("<th>", { class: "text-center" }).text(__("Pending")))
            .append($("<th>", { class: "text-center" }).text(__("In preparation")))
            .append($("<th>", { class: "text-center" }).text(__("Total")));
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
                    .append($("<td>", { class: "text-center production-qty total" }).text(this.format_qty(row.total_qty)))
            );
        });
        table.append(body);
        content.append($("<div>", { class: "table-responsive" }).append(table));
    }

    render_commands(content, commands, attended) {
        if (!commands.length) {
            this.render_empty(
                content,
                attended ? __("There are no attended orders today") : __("There are no active commands")
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
            const row = $("<div>", { class: "production-command-item" }).append(
                $("<strong>", { class: "production-command-item-qty" }).text(`[${this.format_qty(item.qty)}]`),
                $("<span>", { class: "production-command-item-name" }).text(item.item_name || item.item_code)
            );
            if (!attended && this.dashboard.can_transition && command.next_status) {
                row.append(
                    $("<button>", {
                        type: "button",
                        class: "btn btn-xs btn-default production-item-action"
                    })
                        .data("command-key", command.key)
                        .data("item-identifier", item.identifier)
                        .text(this.action_label(command.next_status, true))
                );
            }
            if (item.notes) row.append($("<small>", { class: "production-command-note" }).text(item.notes));
            item_list.append(row);
        });
        card.append(item_list);

        const footer = $("<footer>", { class: "production-command-footer" }).append(
            $("<span>").text(__("Dishes: {0}", [this.format_qty(command.qty || 0)]))
        );
        if (
            !attended &&
            this.dashboard.can_transition &&
            command.next_status &&
            command.identifiers.length > 1
        ) {
            footer.append(
                $("<button>", {
                    type: "button",
                    class: "btn btn-primary production-command-action"
                })
                    .data("command-key", command.key)
                    .text(this.action_label(command.next_status, false))
            );
        }
        card.append(footer);
        return card;
    }

    transition_items(command, identifiers, single_item) {
        if (this.transitioning || !identifiers || !identifiers.length) return;
        this.transitioning = true;
        this.root().find(".production-command-action, .production-item-action").prop("disabled", true);
        RM.working(single_item ? __("Updating dish") : __("Updating command"), false);
        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "set_commands_status",
            args: {
                identifiers: identifiers,
                expected_status: command.status
            },
            always: response => {
                this.transitioning = false;
                RM.ready();
                if (response && !response.exc && response.message) {
                    frappe.show_alert({
                        message: single_item
                            ? __("Dish updated to {0}", [this.status_label(response.message.status)])
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

    status_label(status) {
        return {
            Sent: __("Pending"),
            Processing: __("In preparation"),
            Completed: __("Attended"),
            Delivering: __("Delivering"),
            Delivered: __("Delivered")
        }[status] || status;
    }

    format_qty(value) {
        const number = Number(value || 0);
        return Number.isInteger(number) ? number : number.toFixed(2);
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
