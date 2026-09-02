function restaurant_payment_amount(value) {
    const parsed_value = parseFloat(String(value ?? "").replace(",", "."));
    if (!Number.isFinite(parsed_value) || parsed_value <= 0) return 0;
    return Math.round((parsed_value + Number.EPSILON) * 100) / 100;
}

function restaurant_payment_input_value(pad_editing, internal_value, visible_value) {
    return pad_editing ? internal_value : visible_value;
}

function restaurant_normalize_payment_allocations(allocations = {}) {
    return Object.entries(allocations).reduce((normalized, [method, value]) => {
        const amount = restaurant_payment_amount(value);
        if (method && amount > 0) normalized[method] = amount;
        return normalized;
    }, {});
}

function restaurant_payment_distribution(payable_amount, allocations = {}) {
    const payments = restaurant_normalize_payment_allocations(allocations);
    const payable = restaurant_payment_amount(payable_amount);
    const paid = restaurant_payment_amount(
        Object.values(payments).reduce((total, value) => total + value, 0)
    );

    return {
        payments,
        paid,
        pending: restaurant_payment_amount(payable - paid),
        change: restaurant_payment_amount(paid - payable)
    };
}

class PayForm extends DeskForm {
    button_payment = null;
    num_pad = null;
    payment_allocations = {};
    payment_method_select = null;
    payment_amount_input = null;
    payment_summary_wrapper = null;
    payment_totals_wrapper = null;
    active_payment_method = null;
    guest_count = null;
    discount_global_percent = null;
    tip_amount_input = null;
    tip_mode_of_payment = null;
    form_name = "Payment Order";
    has_primary_action = false;

    get payable_amount() {
        const order_amount = flt(this.order && this.order.amount);
        const discount_percent = flt(this.order && this.order.data.discount_global_percent);
        const discount_amount = flt(this.order && this.order.data.discount);

        if (discount_percent > 0) {
            return Math.max(flt(order_amount * (1 - discount_percent / 100), 2), 0);
        }
        return Math.max(flt(order_amount - discount_amount, 2), 0);
    }

    get tips_enabled() {
        return Boolean(Number(RM.restrictions && RM.restrictions.enable_tips));
    }

    get tip_amount() {
        if (!this.tips_enabled || !this.tip_amount_input) return 0;
        return Math.max(flt(this.tip_amount_input.float_val, 2), 0);
    }

    get total_charge_amount() {
        return flt(this.payable_amount + this.tip_amount, 2);
    }

    constructor(options) {
        super(options);

        this.doc_name = this.order.data.name;
        this.title = this.order.data.name;
        this.primary_action = () => {
            this.send_payment();
        };

        this.primary_action_label = __("Pay");

        super.initialize();
    }

    async make() {
        await super.make();

        this.init_synchronize();

        setTimeout(() => {
            this.make_inputs();
            this.make_pad();
            this.make_payment_button();
        }, 200);

        this.fields_dict.address.df.onchange = () => {
            frappe.call({
                method: 'frappe.contacts.doctype.address.address.get_address_display',
                args: {
                    "address_dict": this.get_value("address")
                },
                callback: (r) => {
                    this.set_value("primary_address", r.message);
                }
            });
        }
    }

    init_synchronize() {
        frappe.realtime.on("pos_profile_update", () => {
            this.hide();
        });
    }

    make_pad() {
        this.num_pad = new NumPad({
            on_enter: () => {
                this.update_paid_value();
            }
        });

        const $numpad_wrapper = this.get_field("num_pad").$wrapper;
        $numpad_wrapper
            .empty()
            .addClass("restaurant-numpad")
            .append(
                $("<div>", { class: "restaurant-numpad-surface" })
                    .append(this.num_pad.html)
            );

        const $payment_column = this.get_field("payment_methods").$wrapper.parent().parent();
        const $numpad_column = $numpad_wrapper.parent().parent();
        $payment_column
            .removeClass("col col-sm-6")
            .addClass("restaurant-payment-column");
        $numpad_column
            .removeClass("col col-sm-6")
            .addClass("restaurant-numpad-column")
            .css("max-width", "");
        $payment_column.parent().addClass("restaurant-payment-layout");
    }

    async reload(){
        await super.reload(null, true);

        this.set_guest_count_input();
        this.set_receipt_defaults();
        // this.set_discount_global_percent_input();
        this.update_paid_value();
        this.refresh_payment_button_amount();
    }


    make_inputs() {
        const payment_methods = this.available_payment_methods;
        const default_method = this.default_payment_method;
        this.payment_allocations = {};
        this.active_payment_method = default_method;

        this.payment_method_select = $("<select>", {
            class: "form-control restaurant-payment-method-select",
            "aria-label": __("Mode of Payment")
        });
        payment_methods.forEach((method) => {
            this.payment_method_select.append($("<option>", { value: method, text: method }));
        });
        this.payment_method_select.on("change", () => {
            this.select_payment_method(this.payment_method_select.val());
        });

        this.payment_amount_input = frappe.jshtml({
            tag: "input",
            properties: {
                type: "text",
                class: "input-with-feedback form-control bold restaurant-payment-amount",
                placeholder: "0.00"
            },
        }).on(["change", "keyup"], () => {
            const value = restaurant_payment_input_value(
                this.payment_amount_input.pad_editing,
                this.payment_amount_input.float_val,
                this.payment_amount_input.JQ().val()
            );
            this.set_active_payment_allocation(value);
        }).on("click", (input) => {
            this.num_pad.input = input;
        }).float();

        const $payment_section = $("<div>", { class: "restaurant-payment-editor" });
        const $editor_grid = $("<div>", { class: "restaurant-payment-editor-grid" });
        const $method_field = $("<div>", {
            class: "form-group mb-0 restaurant-payment-method-field"
        }).append(
            $("<label>", { class: "control-label", text: __("Mode of Payment") }),
            $("<div>", { class: "control-input-wrapper" }).append(this.payment_method_select)
        );
        const $amount_field = $("<div>", {
            class: "form-group mb-0 restaurant-payment-amount-field"
        }).append(
            $("<label>", { class: "control-label", text: __("Amount") }),
            $("<div>", { class: "control-input-wrapper" }).append(this.payment_amount_input.html())
        );
        const $add_button = $("<button>", {
            type: "button",
            class: "btn btn-default restaurant-payment-add"
        }).append(
            $("<span>", { class: "fa fa-plus" }),
            document.createTextNode(" " + __("Add"))
        ).on("click", () => this.add_next_payment_method());

        this.payment_summary_wrapper = $("<div>", {
            class: "restaurant-payment-summary",
            "aria-live": "polite"
        });
        this.payment_totals_wrapper = $("<div>", {
            class: "restaurant-payment-totals",
            "aria-live": "polite"
        });
        $editor_grid.append($method_field, $amount_field, $add_button);
        $payment_section.append(
            $editor_grid,
            this.payment_summary_wrapper,
            this.payment_totals_wrapper
        );

        const $payment_wrapper = this.get_field("payment_methods").$wrapper;
        $payment_wrapper.empty().append($payment_section);
        this.make_tip_inputs($payment_wrapper);

        this.set_guest_count_input();
        this.set_receipt_defaults();

        if (default_method) {
            this.payment_allocations[default_method] = this.payable_amount;
            this.select_payment_method(default_method, false);
            setTimeout(() => {
                this.payment_amount_input.select();
                this.num_pad.input = this.payment_amount_input;
            }, 200);
        }
        this.update_paid_value();
    }

    get available_payment_methods() {
        return (RM.pos_profile.payments || [])
            .map((payment_method) => payment_method.mode_of_payment)
            .filter(Boolean);
    }

    get default_payment_method() {
        const configured_default = (RM.pos_profile.payments || []).find(
            (payment_method) => payment_method.default === 1
        );
        return configured_default
            ? configured_default.mode_of_payment
            : this.available_payment_methods[0] || null;
    }

    get payment_distribution() {
        return restaurant_payment_distribution(this.payable_amount, this.payment_allocations);
    }

    select_payment_method(method, allocate_pending = true) {
        if (!this.available_payment_methods.includes(method)) return;

        this.active_payment_method = method;
        this.payment_method_select.val(method);
        let allocation_changed = false;
        if (allocate_pending && !restaurant_payment_amount(this.payment_allocations[method])) {
            this.payment_allocations[method] = this.payment_distribution.pending;
            allocation_changed = true;
        }

        this.payment_amount_input.val(
            restaurant_payment_amount(this.payment_allocations[method]).toFixed(2),
            false
        );
        if (this.num_pad) this.num_pad.input = this.payment_amount_input;
        if (allocation_changed) {
            this.update_paid_value();
        } else {
            this.render_payment_allocations();
            this.render_payment_totals();
        }
    }

    set_active_payment_allocation(value) {
        if (!this.active_payment_method) return;
        this.payment_allocations[this.active_payment_method] = restaurant_payment_amount(value);
        this.update_paid_value();
    }

    add_next_payment_method() {
        const next_method = this.available_payment_methods.find(
            (method) => method !== this.active_payment_method
                && !restaurant_payment_amount(this.payment_allocations[method])
        );
        if (!next_method) {
            frappe.show_alert({
                message: __("All payment methods are already included"),
                indicator: "blue"
            });
            return;
        }

        this.select_payment_method(next_method);
        this.payment_amount_input.select();
    }

    remove_payment_allocation(method) {
        delete this.payment_allocations[method];
        if (this.active_payment_method === method) {
            this.payment_amount_input.val("0.00", false);
        }
        this.update_paid_value();
    }

    render_payment_allocations() {
        if (!this.payment_summary_wrapper) return;
        this.payment_summary_wrapper.empty();

        Object.entries(this.payment_distribution.payments).forEach(([method, amount]) => {
            const active_class = method === this.active_payment_method ? " is-active" : "";
            const $row = $("<div>", {
                class: "restaurant-payment-row" + active_class
            });
            const $select = $("<button>", {
                type: "button",
                class: "btn btn-link restaurant-payment-row-method"
            }).append(
                $("<span>", { class: "restaurant-payment-row-name", text: method }),
                $("<strong>", { text: RM.format_currency(amount) })
            ).on("click", () => this.select_payment_method(method, false));
            const $remove = $("<button>", {
                type: "button",
                class: "btn btn-link text-danger restaurant-payment-remove",
                title: __("Remove payment method"),
                "aria-label": __("Remove payment method {0}", [method])
            }).append($("<span>", { class: "fa fa-trash" }))
                .on("click", () => this.remove_payment_allocation(method));

            this.payment_summary_wrapper.append($row.append($select, $remove));
        });
    }

    render_payment_totals() {
        if (!this.payment_totals_wrapper) return;
        const distribution = this.payment_distribution;
        const totals = [
            [__("Paid"), distribution.paid, "paid"],
            [__("Pending"), distribution.pending, "pending"],
            [__("Change"), distribution.change, "change"]
        ];

        this.payment_totals_wrapper.empty();
        totals.forEach(([label, amount, modifier]) => {
            this.payment_totals_wrapper.append(
                $("<div>", {
                    class: "restaurant-payment-total is-" + modifier
                }).append(
                    $("<span>", { text: label }),
                    $("<strong>", { text: RM.format_currency(amount) })
                )
            );
        });
    }

    make_tip_inputs($payment_wrapper) {
        this.tip_amount_input = null;
        this.tip_mode_of_payment = null;
        if (!this.tips_enabled) return;

        this.tip_amount_input = frappe.jshtml({
            tag: "input",
            properties: {
                type: "text",
                class: "input-with-feedback form-control bold",
                placeholder: "0.00"
            },
        }).on(["change", "keyup"], () => {
            this.update_paid_value();
        }).on("click", (obj) => {
            this.num_pad.input = obj;
        }).float();

        this.tip_mode_of_payment = $("<select>", {
            class: "form-control",
            "aria-label": __("Tip collection method")
        });
        RM.pos_profile.payments.forEach((payment_method) => {
            this.tip_mode_of_payment.append(
                $("<option>", {
                    value: payment_method.mode_of_payment,
                    text: payment_method.mode_of_payment
                })
            );
        });
        const default_method = RM.pos_profile.payments.find(
            (payment_method) => payment_method.default === 1
        );
        if (default_method) {
            this.tip_mode_of_payment.val(default_method.mode_of_payment);
        }
        this.tip_mode_of_payment.on("change", () => this.refresh_payment_button_amount());

        const $tip_section = $(`
            <div class="restaurant-tip-payment border-top pt-3 mt-3">
                <div class="form-group restaurant-tip-amount">
                    <label class="control-label">${__("Tip")}</label>
                    <div class="control-input-wrapper"></div>
                    <small class="text-muted">${__("The tip is collected separately and is not part of the fiscal sale.")}</small>
                </div>
                <div class="form-group restaurant-tip-method">
                    <label class="control-label">${__("Tip collection method")}</label>
                    <div class="control-input-wrapper"></div>
                </div>
            </div>
        `);
        $tip_section.find(".restaurant-tip-amount .control-input-wrapper")
            .append(this.tip_amount_input.html());
        $tip_section.find(".restaurant-tip-method .control-input-wrapper")
            .append(this.tip_mode_of_payment);
        $payment_wrapper.append($tip_section);
    }

    set_guest_count_input(){
        if (this.order.data.service_type && this.order.data.service_type !== "Dine In") {
            this.guest_count = frappe.jshtml({
                tag: "input",
                properties: { type: "hidden" }
            }).val("0").int();
            this.get_field("guest_count").$wrapper.empty().append(this.guest_count.html());
            this.get_field("guest_count").$wrapper.parent().hide();
            return;
        }
        this.get_field("guest_count").$wrapper.parent().show();
        if(this.doc.guest_count == 0){
            this.guest_count = frappe.jshtml({
                tag: "input",
                properties: {
                    type: "text",
                    class: `input-with-feedback form-control bold`
                },
            }).on("click", (obj) => {
                this.num_pad.input = obj;
            }).val("1").int();
        } else{
            this.guest_count = frappe.jshtml({
                tag: "input",
                properties: {
                    type: "text",
                    class: `input-with-feedback form-control bold`
                },
            }).on("click", (obj) => {
                this.num_pad.input = obj;
            }).val(this.doc.guest_count).int();
        }
        this.get_field("guest_count").$wrapper.empty().append(
            this.form_tag("Guest Count", this.guest_count)
        );
    }

    set_receipt_defaults() {
        if (!this.get_value("voucher_type")) {
            this.set_value("voucher_type", "Boleta");
        }
        if (!this.get_value("emission_mode")) {
            this.set_value("emission_mode", "Electrónica");
        }
    }

    form_tag(label, input) {
        return `
        <div class="form-group">
            <div class="clearfix">
                <label class="control-label" style="padding-right: 0;">${__(label)}</label>
            </div>
            <div class="control-input-wrapper">
                ${input.html()}
            </div>
         </div>`
    }

    make_payment_button() {
        this.button_payment = frappe.jshtml({
            tag: "button",
            wrapper: this.get_field("payment_button").$wrapper,
            properties: {
                type: "button",
                class: `btn btn-primary btn-lg btn-flat`,
                style: "width: 100%; height: 60px;"
            },
            content: `<span style="font-size: 25px; font-weight: 400">{{text}}</span>`,
            text: this.payment_button_label
        }).on("click", () => {
            if (!RM.can_pay_order(this.order)) return;
            this.button_payment.disable().val(__("Paying"));
            this.send_payment();
        }, !RM.restrictions.to_pay ? DOUBLE_CLICK : null).prop("disabled", !RM.can_pay_order(this.order));
    }

    get payment_button_label() {
        return `${__("Pay")} S/ ${this.total_charge_amount.toFixed(2)}`;
    }

    refresh_payment_button_amount() {
        if (this.button_payment) {
            this.button_payment.val(this.payment_button_label, false);
        }
    }

    get payments_values() {
        return this.payment_distribution.payments;
    }

    send_payment() {
        RM.working("Saving Invoice");
        this.#send_payment();
    }

    reset_payment_button() {
        RM.ready();
        if (!RM.can_pay_order(this.order)) {
            this.button_payment.disable();
            return;
        }
        this.button_payment.enable().remove_class("btn-warning");
        this.refresh_payment_button_amount();
    }

    #send_payment() {
        if (!RM.can_pay_order(this.order)) return;
        const order_manage = this.order.order_manage;
        const voucher_type = this.get_value("voucher_type");
        const emission_mode = this.get_value("emission_mode");

        if (!voucher_type || !emission_mode) {
            frappe.msgprint(__("Seleccione el tipo de comprobante y el modo de emisión"));
            this.reset_payment_button();
            return;
        }

        let suma_valor = 0;
        Object.values(this.payments_values).forEach((value) => {
            suma_valor += flt(value);
        });
        if(suma_valor == 0.01){
            suma_valor = 0;
        }
        const payable_amount = this.payable_amount;
        if (this.tip_amount > 0 && !this.tip_mode_of_payment.val()) {
            frappe.msgprint(__("Seleccione el medio de cobro de la propina"));
            this.reset_payment_button();
            return;
        }
        if(Math.abs(suma_valor - payable_amount) > 0.005){
            frappe.msgprint(__("El pago debe ser {0}", [RM.format_currency(payable_amount)]));
            this.reset_payment_button();
        }
        else{

        RM.working("Generating Invoice");
        this.order.data.guest_count = this.guest_count.val();
        this.order.data.voucher_type = voucher_type;
        this.order.data.emission_mode = emission_mode;
        frappeHelper.api.call({
            model: "Table Order",
            name: this.order.data.name,
            method: "make_invoice",
            args: {
                mode_of_payment: this.payments_values,
                customer: this.get_value("customer"),
                guest_count: this.guest_count.float_val,
                voucher_type: voucher_type,
                emission_mode: emission_mode,
                tip_amount: this.tip_amount,
                tip_mode_of_payment: this.tip_amount > 0
                    ? this.tip_mode_of_payment.val()
                    : null
            },
            always: (r) => {
                RM.ready();
                
                if (r.message && r.message.status) {
                    if (r.message.tip_status === "Pending Accounting") {
                        frappe.msgprint({
                            title: __("Propina pendiente de contabilización"),
                            message: __("El comprobante fue generado, pero la propina requiere regularización contable."),
                            indicator: "orange"
                        });
                    }
                    this.hide();
                    try {
                        order_manage.clear_current_order();
                        order_manage.check_buttons_status();
                        order_manage.check_item_editor_status();
                        order_manage.make_orders();
                    } catch (error) {
                        console.error("Could not clean up the paid order", error);
                    }

                    if (emission_mode !== "Electrónica") {
                        RM.ready();
                        return;
                    }

                    // Electronic issuance is orchestrated on the server so consultation,
                    // submission, persistence, and printing cannot be interrupted between requests.
                    RM.working("Generating Invoice Electronic");
                    frappe.call({
                        method: "restaurant_management.printing.process_pos_invoice_electronic",
                        args: {
                            invoice_name: r.message.invoice_name
                        },
                        callback: function(response) {
                            try {
                                const result = response.message || {};
                                if (!result.processed) {
                                    frappe.msgprint({
                                        title: __("Comprobante pendiente de envío"),
                                        message: result.message || __(
                                            "Nubefact no confirmó el comprobante electrónico"
                                        ),
                                        indicator: "orange"
                                    });
                                    return;
                                }

                                const print_result = result.print_queue || {};
                                frappe.show_alert({
                                    message: print_result.queued
                                        ? __("Electronic receipt queued for printing")
                                        : __("Electronic receipt generated"),
                                    indicator: "green"
                                });
                            } finally {
                                RM.ready();
                            }
                        },
                        error: function(error) {
                            console.error("Electronic receipt processing failed", error);
                            RM.ready();
                        }
                    });
                } else {
                    this.reset_payment_button();
                }
            },
            freeze: true
        });}
    }

    make_pad() {
        this.num_pad = new NumPad({
            on_enter: () => {
                this.update_paid_value();
            }
        });

        const $numpad_wrapper = this.get_field("num_pad").$wrapper;
        $numpad_wrapper
            .empty()
            .addClass("restaurant-numpad")
            .append(
                $("<div>", { class: "restaurant-numpad-surface" })
                    .append(this.num_pad.html)
            );

        const $payment_column = this.get_field("payment_methods").$wrapper.parent().parent();
        const $numpad_column = $numpad_wrapper.parent().parent();
        $payment_column
            .removeClass("col col-sm-6")
            .addClass("restaurant-payment-column");
        $numpad_column
            .removeClass("col col-sm-6")
            .addClass("restaurant-numpad-column")
            .css("max-width", "");
        $payment_column.parent().addClass("restaurant-payment-layout");
    }
    // TIDAX
    print_invoice_silent(invoice_name){
        if (!RM.can_pay_order(this.order)) return;
        return frappe.call({
            method: "restaurant_management.printing.queue_invoice_print",
            type: "POST",
            args: {invoice_name},
            callback: r => {
                if (r.message && r.message.queued) {
                    frappe.show_alert({message: __("Electronic receipt queued for printing"), indicator: "green"});
                }
            }
        });
    }

    print(invoice_name) {
        if (!RM.can_pay_order(this.order)) return;
        //TIDAX
        var formato_impresion;
        frappe.call({
            method: "restaurant_management.restaurant_management.doctype.utils.obtener_res_set",
            args: {
                filtro: "print_format_ce",
                invoice: invoice_name
            },
            callback: function(r) {
                if (r.message) {
                    formato_impresion = r.message[0].value;
                }
                else {
                    frappe.msgprint("El formato no pudo ser encontrado");
                }
            },
            async: false
        });

        // frappe.call({
        //     method: 'silent_print.utils.print_format.print_silently',
        //     args: {
        //         doctype: "POS INVOICE",
        //         name: invoice_name,
        //         print_format: formato_impresion,
        //         print_type: "INVOICE"
        //     },
        //     async: false
        // });

        const title = invoice_name + " (" + __("Print") + ")";
        const order_manage = this.order.order_manage;

        const props = {
            model: "POS Invoice",
            model_name: invoice_name,
            args: {
                format: formato_impresion,
                _lang: RM.lang,
                no_letterhead: RM.pos_profile.letter_head || 1,
                letterhead: RM.pos_profile.letter_head || 'No%20Letterhead'
            },
            from_server: true,
            set_buttons: true,
            is_pdf: true,
            customize: true,
            title: title
        };

        if (order_manage.print_modal) {
            order_manage.print_modal.set_props(props);
            order_manage.print_modal.set_title(title);
            order_manage.print_modal.reload().show();
        } else {
            order_manage.print_modal = new DeskModal(props);
        }
    }

    update_paid_value() {
        const distribution = this.payment_distribution;
        this.set_value("amount", this.payable_amount);
        this.set_value("total_payment", distribution.paid);
        this.set_value("change_amount", distribution.change);
        this.render_payment_allocations();
        this.render_payment_totals();
        this.refresh_payment_button_amount();
    }
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = {
        restaurant_payment_amount,
        restaurant_payment_input_value,
        restaurant_normalize_payment_allocations,
        restaurant_payment_distribution
    };
}
