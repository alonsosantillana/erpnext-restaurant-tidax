class PayForm extends DeskForm {
    button_payment = null;
    num_pad = null;
    payment_methods = {};
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

        this.get_field("num_pad").$wrapper.empty().append(
            `<div style="width: 100% !important; height: 200px !important; padding: 0">
                ${this.num_pad.html}
            </div>`
        );

        this.get_field("num_pad").$wrapper.parent().parent().css("max-width", "300px");
        this.get_field("payment_methods").$wrapper.parent().parent().removeClass("col-sm-6").addClass("col");
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
        let payment_methods = "";
        let total_con_desc = 0;
        RM.pos_profile.payments.forEach(mode_of_payment => {
            this.payment_methods[mode_of_payment.mode_of_payment] = frappe.jshtml({
                tag: "input",
                properties: {
                    type: "text",
                    class: `input-with-feedback form-control bold`
                },
            }).on(["change", "keyup"], () => {
                this.update_paid_value();
            }).on("click", (obj) => {
                this.num_pad.input = obj;
            }).float();

            if (mode_of_payment.default === 1) {
                // TIDAX: Poner el pago total en automatico en el metodo de pago por default
                // if(this.doc.discount > 0) {
                //     total_con_desc = this.order.data.amount - this.doc.discount
                //     this.payment_methods[mode_of_payment.mode_of_payment].val(total_con_desc);
                // }
                // else if(this.doc.discount_global_percent > 0){
                //     total_con_desc = this.order.data.amount*(1-(this.doc.discount_global_percent/100));
                //     this.payment_methods[mode_of_payment.mode_of_payment].val(total_con_desc);
                // }
                // else{
                //     this.payment_methods[mode_of_payment.mode_of_payment].val(this.order.data.amount);
                // }

                setTimeout(() => {
                    this.payment_methods[mode_of_payment.mode_of_payment].select();
                    this.num_pad.input = this.payment_methods[mode_of_payment.mode_of_payment];
                }, 200);
            }

            payment_methods += this.form_tag (
                mode_of_payment.mode_of_payment, this.payment_methods[mode_of_payment.mode_of_payment]
            );
        });

        const $payment_wrapper = this.get_field("payment_methods").$wrapper;
        $payment_wrapper.empty().append(payment_methods);
        this.make_tip_inputs($payment_wrapper);

        this.set_guest_count_input();
        this.set_receipt_defaults();

        // this.set_discount_global_percent_input();
        
        this.update_paid_value();

        /*RM.pos_profile.payments.forEach(mode_of_payment => {
            console.log(this.payment_methods[mode_of_payment.mode_of_payment])
        });*/
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
            if (!RM.can_pay) return;
            this.button_payment.disable().val(__("Paying"));
            this.send_payment();
        }, !RM.restrictions.to_pay ? DOUBLE_CLICK : null).prop("disabled", !RM.can_pay);
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
        const payment_values = {};
        RM.pos_profile.payments.forEach((mode_of_payment) => {
            let value = this.payment_methods[mode_of_payment.mode_of_payment].float_val;
            if (value > 0) {
                payment_values[mode_of_payment.mode_of_payment] = value;
            }
        });
        
        return payment_values;
    }

    send_payment() {
        RM.working("Saving Invoice");
        this.#send_payment();
    }

    reset_payment_button() {
        RM.ready();
        if (!RM.can_pay) {
            this.button_payment.disable();
            return;
        }
        this.button_payment.enable().remove_class("btn-warning");
        this.refresh_payment_button_amount();
    }

    #send_payment() {
        if (!RM.can_pay) return;
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
                    order_manage.clear_current_order();
                    order_manage.check_buttons_status();
                    order_manage.check_item_editor_status();
                    
                    this.hide();

                    order_manage.make_orders();

                    if (emission_mode !== "Electrónica") {
                        RM.ready();
                        return;
                    }

                    // TIDAX
                    RM.working("Generating Invoice Electronic");
                    var com = RM.company;

                    new Promise(function(resolve, reject) {
                        frappe.call({
                            method: "ovenube_peru.nubefact_integration.facturacion_electronica.consult_document",
                            args: {
                                'company': com,
                                'invoice': r.message.invoice_name,
                                'doctype': "POS Invoice"
                            },
                            callback: function(values) {
                                //console.log(values.message.codigo);
                                resolve(values);
                            }
                        });
                    }).then(function(values) {
                        if (values.message.codigo == "24"){
                            frappe.call({
                                method: "ovenube_peru.nubefact_integration.facturacion_electronica.send_document",
                                args: {
                                    'company': com,
                                    'invoice': r.message.invoice_name,
                                    'doctype': "POS Invoice"
                                },
                                callback: function(data) {
                                    if (data.message.codigo_hash) {
                                        RM.working("Sinchronizing Invoice Electronic");
                                        let estado = (data.message.codigo_hash != "") ? ("Aceptado") : ("Rechazado");

                                        frappe.call({
                                            method: "ovenube_peru.nubefact_integration.facturacion_electronica.update_pos_invoice_ce",
                                            args: {
                                                'company': com,
                                                'invoice': r.message.invoice_name,
                                                'doctype': "POS Invoice",
                                                'estado_sunat': estado,
                                                //'sunat_descripcion': data.message.sunat_descripcion,
                                                'cadena_para_codigo_qr': data.message.cadena_para_codigo_qr,
                                                //'codigo_de_barras': data.message.codigo_de_barras,
                                                'codigo_hash': data.message.codigo_hash,
                                                'enlace_del_pdf': data.message.enlace_del_pdf
                                            },
                                            callback: function(data) {
                                                //console.log(data);
                                                if (data.message.codigo_hash) {                                                    
                                                    //window.open(data.message.enlace_del_pdf);
                                                    console.log("CE Generado");
                                                } else{
                                                    frappe.validated = false;
                                                    frappe.throw(data.message.errors);
                                                }
                                            }
                                        });
                                        //window.open(data.message.enlace_del_pdf);
                                        //this.print_invoice_silent(r.message.invoice_name);
                                    } else{
                                        frappe.validated = false;
                                        frappe.throw(data.message.errors);
                                    }
                                    RM.ready();
                                }
                            });
                        } else {
                            // frappe.model.set_value(cdt, cdn, "estado_sunat", (values.message.codigo_hash != "") ? ("Aceptado") : ("Rechazado"));
                            // frappe.model.set_value(cdt, cdn, "respuesta_sunat", values.message.sunat_descripcion);
                            // frappe.model.set_value(cdt, cdn, "codigo_qr_sunat", values.message.cadena_para_codigo_qr);
                            // frappe.model.set_value(cdt, cdn, "codigo_barras_sunat", values.message.codigo_de_barras);
                            // frappe.model.set_value(cdt, cdn, "codigo_hash_sunat", values.message.codigo_hash);
                            // frappe.model.set_value(cdt, cdn, "enlace_pdf", values.message.enlace_del_pdf);
                            RM.working("Ready");
                            // window.open(values.message.enlace_del_pdf);
                        }
                    });
                    // this.print_invoice_silent(r.message.invoice_name);
                    // this.print(r.message.invoice_name);
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

        this.get_field("num_pad").$wrapper.empty().append(
            `<div style="width: 100% !important; height: 200px !important; padding: 0">
                ${this.num_pad.html}
            </div>`
        );

        this.get_field("num_pad").$wrapper.parent().parent().css("max-width", "300px");
        this.get_field("payment_methods").$wrapper.parent().parent().removeClass("col-sm-6").addClass("col");
    }
    // TIDAX
    print_invoice_silent(invoice_name){
        if (!RM.can_pay) return;
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
                    frappe.call({
                        method: 'silent_print.utils.print_format.print_silently',
                        args: {
                            doctype: "POS INVOICE",
                            name: invoice_name,
                            print_format: formato_impresion,
                            print_type: "INVOICE"
                        }
                    });
                }
                else {
                    frappe.msgprint("El formato no pudo ser encontrado");
                }
            },
            async: false
        });
    }

    print(invoice_name) {
        if (!RM.can_pay) return;
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

    //TIDAX
    update_paid_value() {
        let total = 0;
        setTimeout(() => {
            Object.keys(this.payment_methods).forEach((payment_method) => {
                total += flt(this.payment_methods[payment_method].float_val);
            });

            const payable_amount = this.payable_amount;
            this.set_value("amount", payable_amount);
            this.set_value("total_payment", total);
            this.set_value("change_amount", flt(total - payable_amount, 2));
            this.refresh_payment_button_amount();
        }, 0);
    }
    // update_paid_value() {
    //     let total = 0;

    //     setTimeout(() => {
    //         Object.keys(this.payment_methods).forEach((payment_method) => {
    //             total += this.payment_methods[payment_method].float_val;
    //         });

    //         this.set_value("total_payment", total);
    //         this.set_value("change_amount", (total - this.order.amount));
    //     }, 0);
    // }
}
