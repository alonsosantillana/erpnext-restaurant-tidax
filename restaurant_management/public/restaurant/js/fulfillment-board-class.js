class FulfillmentBoard {
    constructor(options) {
        Object.assign(this, options);
        this.fulfillment_type = null;
        this.reload_timer = null;
        this.counts_timer = null;
        this.counts = { Delivery: 0, Pickup: 0 };
        this.enabled_types = this.enabled_types || ["Delivery", "Pickup"];
        this.order_managers = {};
        this.columns = {
            Delivery: ["New", "Preparing", "Ready", "Assigned", "Out for Delivery", "Delivery Failed"],
            Pickup: ["New", "Preparing", "Ready", "Picked Up"]
        };
        this.make();
        this.init_realtime();
        this.init_reconciliation();
    }

    make() {
        this.wrapper = $("<div>").addClass("fulfillment-board hide");
        this.toolbar = $("<div>").addClass("fulfillment-toolbar");
        this.title = $("<h4>").addClass("fulfillment-title");
        this.back_button = $("<button>")
            .attr({ type: "button", "aria-label": "Volver a pedidos externos" })
            .addClass("btn btn-default btn-sm fulfillment-back-button")
            .append($("<span>").addClass("fa fa-arrow-left"), document.createTextNode(" Pedidos externos"))
            .on("click", () => { if (this.on_back) this.on_back(); });
        this.refresh_button = $("<button>")
            .addClass("btn btn-default btn-sm")
            .append($("<span>").addClass("fa fa-refresh"), document.createTextNode(" " + __("Refresh")))
            .on("click", () => this.reload());
        this.new_button = $("<button>")
            .addClass("btn btn-primary btn-sm")
            .append($("<span>").addClass("fa fa-plus"), document.createTextNode(" " + __("New order")))
            .on("click", () => this.new_order());
        const heading = $("<div>").addClass("fulfillment-toolbar-heading").append(this.back_button, this.title);
        this.toolbar.append(heading, $("<div>").addClass("fulfillment-toolbar-actions").append(this.refresh_button, " ", this.new_button));
        this.columns_wrapper = $("<div>").addClass("fulfillment-columns");
        this.wrapper.append(this.toolbar, this.columns_wrapper);
        this.container.append(this.wrapper);
    }

    show(fulfillment_type) {
        this.fulfillment_type = fulfillment_type;
        this.title.text(fulfillment_type === "Delivery" ? "Entrega a domicilio" : "Recojo en local");
        this.new_button.text(fulfillment_type === "Delivery" ? "Nuevo delivery" : "Nuevo recojo");
        this.new_button.prepend($("<span>").addClass("fa fa-plus"), document.createTextNode(" "));
        this.wrapper.removeClass("hide");
        this.reload();
    }

    hide() {
        this.wrapper.addClass("hide");
    }

    reload() {
        if (!this.fulfillment_type || this.wrapper.hasClass("hide")) return;
        this.columns_wrapper.addClass("loading");
        frappe.call({
            method: "restaurant_management.api.get_fulfillment_board",
            args: { fulfillment_type: this.fulfillment_type },
            always: r => {
                this.columns_wrapper.removeClass("loading");
                if (r && Array.isArray(r.message)) {
                    this.counts[this.fulfillment_type] = r.message.length;
                    this.notify_counts();
                    this.render(r.message);
                }
            }
        });
    }

    schedule_reload() {
        clearTimeout(this.reload_timer);
        this.reload_timer = setTimeout(() => this.reload(), 150);
    }

    schedule_counts_refresh() {
        clearTimeout(this.counts_timer);
        this.counts_timer = setTimeout(() => this.refresh_counts(), 150);
    }

    refresh_counts(enabled_types = null) {
        if (enabled_types) this.enabled_types = enabled_types;
        return frappe.call({
            method: "restaurant_management.api.get_fulfillment_counts"
        }).then(r => {
            if (!r.message) return;
            this.counts = {
                Delivery: this.enabled_types.includes("Delivery") ? Number(r.message.Delivery || 0) : 0,
                Pickup: this.enabled_types.includes("Pickup") ? Number(r.message.Pickup || 0) : 0
            };
            this.notify_counts();
        });
    }

    notify_counts() {
        if (this.on_counts_change) this.on_counts_change({ ...this.counts });
    }

    render(rows) {
        this.columns_wrapper.empty();
        const grouped = {};
        this.columns[this.fulfillment_type].forEach(status => grouped[status] = []);
        rows.forEach(row => {
            if (!grouped[row.status]) grouped[row.status] = [];
            grouped[row.status].push(row);
        });

        Object.keys(grouped).forEach(status => {
            const column = $("<section>")
                .addClass("fulfillment-column")
                .addClass(this.status_class(status));
            const header = $("<header>").append(
                $("<span>").text(__(status)),
                $("<span>").addClass("badge").text(grouped[status].length)
            );
            const cards = $("<div>").addClass("fulfillment-card-list");
            grouped[status].forEach(row => cards.append(this.card(row)));
            column.append(header, cards);
            this.columns_wrapper.append(column);
        });
    }

    status_class(status) {
        const slug = String(status || "")
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "");
        return `fulfillment-status-${slug || "unknown"}`;
    }

    card(row) {
        const card = $("<article>")
            .addClass("fulfillment-card")
            .addClass(this.status_class(row.status))
            .attr("tabindex", 0);
        const heading = $("<div>").addClass("fulfillment-card-heading").append(
            $("<strong>").text(row.order),
            $("<span>").addClass("indicator-pill").text(__(row.payment_status || "Unpaid"))
        );
        const customer = $("<div>").addClass("fulfillment-customer").text(row.customer_name || __("Customer"));
        const meta = $("<div>").addClass("fulfillment-meta");
        meta.append($("<span>").text(row.order_channel || ""));
        if (row.promised_at) meta.append($("<span>").text(frappe.datetime.str_to_user(row.promised_at)));
        meta.append($("<span>").text(RM.format_currency(row.amount || 0)));
        if (row.courier_name) meta.append($("<span>").text(row.courier_name));

        const actions = $("<div>").addClass("fulfillment-actions");
        this.add_primary_action(actions, row);
        if (["New", "Preparing", "Ready", "Assigned", "Delivery Failed"].includes(row.status)) {
            $("<button>")
                .addClass("btn btn-xs btn-default")
                .text(__("Cancel"))
                .on("click", event => {
                    event.stopPropagation();
                    this.ask_reason(row, "Cancelled");
                })
                .appendTo(actions);
        }

        card.append(heading, customer, meta, actions);
        card.on("click keydown", event => {
            if (event.type === "keydown" && event.key !== "Enter") return;
            this.open_order(row);
        });
        return card;
    }

    add_primary_action(actions, row) {
        let next_status = null;
        let label = null;
        if (row.fulfillment_type === "Delivery") {
            if (row.status === "Ready") [next_status, label] = ["Assigned", __("Assign")];
            if (row.status === "Assigned") [next_status, label] = ["Out for Delivery", __("Dispatch")];
            if (row.status === "Out for Delivery") [next_status, label] = ["Delivered", __("Delivered")];
            if (row.status === "Delivery Failed") [next_status, label] = ["Assigned", __("Reassign")];
        } else if (row.status === "Ready") {
            [next_status, label] = ["Picked Up", __("Picked up")];
        }
        if (!next_status) return;

        $("<button>")
            .addClass("btn btn-xs btn-primary")
            .text(label)
            .on("click", event => {
                event.stopPropagation();
                if (next_status === "Assigned") this.ask_courier(row);
                else this.transition(row, next_status);
            })
            .appendTo(actions);

        if (row.status === "Out for Delivery") {
            $("<button>")
                .addClass("btn btn-xs btn-warning")
                .text(__("Failed"))
                .on("click", event => {
                    event.stopPropagation();
                    this.ask_reason(row, "Delivery Failed");
                })
                .appendTo(actions);
        }
    }

    ask_courier(row) {
        const dialog = new frappe.ui.Dialog({
            title: __("Assign delivery"),
            fields: [{ fieldname: "courier_name", fieldtype: "Data", label: __("Courier"), reqd: 1 }],
            primary_action_label: __("Assign"),
            primary_action: values => {
                dialog.hide();
                this.transition(row, "Assigned", { courier_name: values.courier_name });
            }
        });
        dialog.show();
    }

    ask_reason(row, next_status) {
        const dialog = new frappe.ui.Dialog({
            title: __(next_status),
            fields: [{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }],
            primary_action_label: __("Confirm"),
            primary_action: values => {
                dialog.hide();
                this.transition(row, next_status, { reason: values.reason });
            }
        });
        dialog.show();
    }

    transition(row, next_status, values = {}) {
        frappe.call({
            method: "restaurant_management.api.call",
            args: {
                model: "Restaurant Fulfillment",
                name: row.name,
                method: "transition_status",
                args: JSON.stringify({
                    next_status,
                    expected_status: row.status,
                    ...values
                })
            },
            freeze: true,
            freeze_message: __("Updating delivery"),
            callback: () => this.schedule_reload()
        });
    }

    new_order() {
        const fulfillment_type = this.fulfillment_type;
        const dialog = new frappe.ui.Dialog({
            title: fulfillment_type === "Delivery" ? __("New delivery") : __("New pickup"),
            fields: [
                { fieldname: "customer", fieldtype: "Link", options: "Customer", label: __("Customer"), reqd: 1 },
                { fieldname: "customer_identity", fieldtype: "Button", label: __("New Customer from DNI/RUC") },
                { fieldname: "contact_phone", fieldtype: "Data", label: __("Contact phone"), reqd: 1 },
                {
                    fieldname: "address", fieldtype: "Link", options: "Address", label: __("Delivery address"),
                    depends_on: "eval:" + JSON.stringify(fulfillment_type === "Delivery"),
                    mandatory_depends_on: "eval:" + JSON.stringify(fulfillment_type === "Delivery"),
                    get_query: () => ({
                        query: "frappe.contacts.doctype.address.address.address_query",
                        filters: { link_doctype: "Customer", link_name: dialog.get_value("customer") }
                    })
                },
                { fieldname: "delivery_reference", fieldtype: "Small Text", label: __("Reference"), depends_on: "eval:" + JSON.stringify(fulfillment_type === "Delivery") },
                { fieldname: "instructions", fieldtype: "Small Text", label: __("Instructions") },
                { fieldname: "order_channel", fieldtype: "Select", label: __("Order channel"), options: "Phone\nWhatsApp\nWeb\nMarketplace\nWalk-in\nOther", default: fulfillment_type === "Pickup" ? "Walk-in" : "Phone", reqd: 1 },
                { fieldname: "promised_at", fieldtype: "Datetime", label: __("Promised at") },
                {
                    fieldname: "delivery_fee", fieldtype: "Currency", label: __("Delivery fee"),
                    default: 0,
                    depends_on: "eval:" + JSON.stringify(fulfillment_type === "Delivery")
                },
                { fieldname: "payment_timing", fieldtype: "Select", label: __("Payment timing"), options: "Prepaid\nCash on Delivery", default: "Prepaid", reqd: 1 },
                { fieldname: "expected_payment_method", fieldtype: "Link", options: "Mode of Payment", label: __("Expected payment method"), mandatory_depends_on: "eval:doc.payment_timing == 'Cash on Delivery'" }
            ],
            primary_action_label: __("Create order"),
            primary_action: values => {
                dialog.disable_primary_action();
                frappe.call({
                    method: "restaurant_management.api.create_fulfillment_order",
                    type: "POST",
                    args: {
                        fulfillment_type,
                        ...values,
                        request_id: RM.uuid("fulfillment")
                    },
                    freeze: true,
                    freeze_message: __("Creating order"),
                    callback: r => {
                        if (!r.message) return;
                        dialog.hide();
                        this.schedule_reload();
                        this.open_order(r.message.fulfillment);
                    },
                    always: () => dialog.enable_primary_action()
                });
            }
        });
        dialog.fields_dict.customer.df.onchange = () => dialog.set_value("address", "");
        dialog.fields_dict.customer_identity.$input.on("click", () => this.customer_from_identity(dialog));
        dialog.show();
    }

    customer_from_identity(order_dialog) {
        const dialog = new frappe.ui.Dialog({
            title: __("New Customer from DNI/RUC"),
            fields: [
                {
                    fieldname: "tax_id", fieldtype: "Data", label: __("DNI or RUC"),
                    description: __("Enter 8 digits for DNI or 11 digits for RUC"), reqd: 1
                },
                { fieldname: "preview", fieldtype: "HTML" }
            ]
        });
        const preview = dialog.fields_dict.preview.$wrapper;
        const add_rows = rows => {
            const table = $("<table>").addClass("table table-bordered").css("margin-top", "10px");
            const body = $("<tbody>").appendTo(table);
            rows.filter(row => row[1]).forEach(row => {
                $("<tr>").append(
                    $("<th>").css("width", "32%").text(row[0]),
                    $("<td>").text(row[1])
                ).appendTo(body);
            });
            preview.append(table);
        };
        const select_customer = result => {
            Promise.resolve(order_dialog.set_value("customer", result.customer.name)).then(() => {
                if (result.address) order_dialog.set_value("address", result.address);
            });
            dialog.hide();
            frappe.show_alert({
                message: result.created
                    ? __("Customer {0} created", [result.customer.customer_name])
                    : __("Customer {0} selected", [result.customer.customer_name]),
                indicator: "green"
            });
        };
        const create_customer = tax_id => {
            dialog.disable_primary_action();
            frappe.call({
                method: "restaurant_management.api.create_customer_from_identity",
                type: "POST",
                args: { tax_id },
                freeze: true,
                freeze_message: __("Creating customer"),
                callback: r => { if (r.message) select_customer(r.message); },
                always: () => dialog.enable_primary_action()
            });
        };
        const render_result = (result, tax_id) => {
            preview.empty();
            dialog.get_primary_btn().removeClass("hide");
            if (result.status === "existing") {
                preview.append($("<div>").addClass("alert alert-info").text(__("This customer already exists")));
                add_rows([
                    [__("Customer"), result.customer.customer_name],
                    [__("DNI or RUC"), result.customer.tax_id]
                ]);
                dialog.set_primary_action(__("Use Customer"), () => select_customer({
                    created: false, customer: result.customer, address: null
                }));
                return;
            }
            if (result.status === "disabled" || result.status === "not_found") {
                const message = result.status === "disabled"
                    ? __("The customer registered with this document is disabled")
                    : __("No information was found for this DNI/RUC");
                preview.append($("<div>").addClass("alert alert-warning").text(message));
                dialog.get_primary_btn().addClass("hide");
                return;
            }
            const identity = result.identity;
            const address = identity.registered_address || {};
            preview.append($("<div>").addClass("alert alert-success").text(
                __("Identity verified. Review the data before creating the customer.")
            ));
            add_rows([
                [__("Document Type"), identity.document_kind],
                [__("DNI or RUC"), identity.tax_id],
                [__("Customer Name"), identity.party_name],
                [__("Registered Address"), address.address_line1],
                [__("District"), address.district],
                [__("Province"), address.province],
                [__("Department"), address.department]
            ]);
            if (result.can_create) {
                dialog.set_primary_action(__("Create Customer"), () => create_customer(tax_id));
            } else {
                preview.append($("<div>").addClass("alert alert-warning").text(
                    __("You do not have permission to create customers")
                ));
                dialog.get_primary_btn().addClass("hide");
            }
        };
        const search = () => {
            const tax_id = String(dialog.get_value("tax_id") || "").trim();
            if (!/^([0-9]{8}|[0-9]{11})$/.test(tax_id)) {
                frappe.msgprint(__("DNI must contain 8 digits and RUC must contain 11 digits"));
                return;
            }
            dialog.disable_primary_action();
            preview.empty().append($("p").addClass("text-muted").text(__("Searching DNI/RUC...")));
            frappe.call({
                method: "restaurant_management.api.lookup_customer_identity",
                args: { tax_id },
                freeze: true,
                freeze_message: __("Searching DNI/RUC"),
                callback: r => { if (r.message) render_result(r.message, tax_id); },
                always: () => dialog.enable_primary_action()
            });
        };
        dialog.set_primary_action(__("Search"), search);
        dialog.fields_dict.tax_id.$input.on("input", () => {
            preview.empty();
            dialog.get_primary_btn().removeClass("hide");
            dialog.set_primary_action(__("Search"), search);
        });
        dialog.show();
        dialog.fields_dict.tax_id.set_focus();
    }

    open_order(row) {
        const fulfillment_name = row.name;
        frappe.call({
            method: "restaurant_management.api.get_fulfillment_detail",
            args: { name: fulfillment_name },
            freeze: true,
            callback: r => {
                if (!r.message) return;
                const order_data = r.message.order.order;
                order_data.name = order_data.name || order_data.data.name;
                const key = `fulfillment-${fulfillment_name}`;
                let manager = this.order_managers[fulfillment_name];
                if (manager) {
                    manager.external_order_data = order_data;
                    manager.show();
                    return;
                }
                const service_label = (row.fulfillment_type || this.fulfillment_type) === "Delivery"
                    ? "Entrega"
                    : "Recojo";
                const virtual_table = {
                    data: {
                        name: key,
                        description: `${service_label} ${order_data.data.short_name}`,
                        current_user: frappe.session.user,
                        orders_count: 1,
                        ordered_items_qty: order_data.data.items_count || 0,
                        type: "Fulfillment"
                    },
                    room: { data: { name: key, description: service_label } },
                    set_orders_count: () => {},
                    synchronize: () => {}
                };
                manager = new OrderManage({
                    table: virtual_table,
                    identifier: RM.OMName(key),
                    external_order_data: order_data,
                    current_order_identifier: order_data.data.name,
                    fulfillment_name
                });
                this.order_managers[fulfillment_name] = manager;
                RM.object(manager.identifier, manager);
            }
        });
    }

    init_reconciliation() {
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) return;
            if (this.wrapper.hasClass("hide")) this.schedule_counts_refresh();
            else this.schedule_reload();
        });
        this.reconciliation_interval = setInterval(() => {
            if (document.hidden) return;
            if (this.wrapper.hasClass("hide")) this.refresh_counts();
            else this.reload();
        }, 5000);
    }

    init_realtime() {
        frappe.realtime.on("restaurant_fulfillment_update", data => {
            if (data && data.name && this.order_managers[data.name]) {
                this.order_managers[data.name].reload_orders_silently();
            }
            this.schedule_counts_refresh();
            if (!data || !data.fulfillment_type || data.fulfillment_type === this.fulfillment_type) {
                this.schedule_reload();
            }
        });
    }
}
