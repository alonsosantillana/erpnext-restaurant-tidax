class PayForm extends DeskForm {
    button_payment = null;
    num_pad = null;
    payment_methods = {};
    dinners = null;
    discount_global_percent = null;
    form_name = "Payment Order";
    has_primary_action = false;
    
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

        this.set_dinners_input();
        // this.set_discount_global_percent_input();
        this.update_paid_value();
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

        this.get_field("payment_methods").$wrapper.empty().append(payment_methods);

        this.set_dinners_input();

        // this.set_discount_global_percent_input();
        
        this.update_paid_value();

        /*RM.pos_profile.payments.forEach(mode_of_payment => {
            console.log(this.payment_methods[mode_of_payment.mode_of_payment])
        });*/
    }

    set_dinners_input(){
        if(this.doc.dinners == 0){
            this.dinners = frappe.jshtml({
                tag: "input",
                properties: {
                    type: "text",
                    class: `input-with-feedback form-control bold`
                },
            }).on("click", (obj) => {
                this.num_pad.input = obj;
            }).val("1").int();
        } else{
            this.dinners = frappe.jshtml({
                tag: "input",
                properties: {
                    type: "text",
                    class: `input-with-feedback form-control bold`
                },
            }).on("click", (obj) => {
                this.num_pad.input = obj;
            }).val(this.doc.dinners).int();
        }
        this.get_field("dinners").$wrapper.empty().append(
            this.form_tag("Dinners", this.dinners)
        );
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
        // TIDAX: MOSTRAR EN BOTON EL IMPORTE DE PAGO
        let importe;
        if(this.doc.discount_global_percent){
            importe = parseFloat(this.doc.amount)*(1-parseFloat(this.doc.discount_global_percent)/100);
            importe = importe.toFixed(2);
        }else if(this.doc.discount){
            importe = parseFloat(this.doc.amount)-(parseFloat(this.doc.discount));
            importe = importe.toFixed(2);
        }else{
            importe = parseFloat(this.doc.amount);
            importe = importe.toFixed(2);
        }

        this.button_payment = frappe.jshtml({
            tag: "button",
            wrapper: this.get_field("payment_button").$wrapper,
            properties: {
                type: "button",
                class: `btn btn-primary btn-lg btn-flat`,
                style: "width: 100%; height: 60px;"
            },
            //content: `<span style="font-size: 25px; font-weight: 400">{{text}} ${this.order.total_money}</span>`,
            content: `<span style="font-size: 25px; font-weight: 400">{{text}} S/ ${importe}</span>`,
            text: `${__("Pay")}`
        }).on("click", () => {
            if (!RM.can_pay) return;
            this.button_payment.disable().val(__("Paying"));
            this.send_payment();
        }, !RM.restrictions.to_pay ? DOUBLE_CLICK : null).prop("disabled", !RM.can_pay);
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
        this.button_payment.enable().val(__("Pay")).remove_class("btn-warning");
    }

    #send_payment() {
        if (!RM.can_pay) return;
        const order_manage = this.order.order_manage;

        // this.payments_values es un objeto JSON
        let suma_valor = 0; // Inicializa la variable suma_valor
        for (let key in this.payments_values) {
            if (this.payments_values.hasOwnProperty(key)) {
                if (key !== "Propinas") {
                    // Accede al valor utilizando la clave (key)
                    let value = this.payments_values[key];
                    suma_valor += value; // Agrega el valor al acumulador suma_valor
                    //alert(`Clave: ${key}, Valor: ${value}, Suma_valor: ${suma_valor}, Total:  ${this.doc.amount}`);
                }
            }
        }
        if(suma_valor == 0.01){
            suma_valor = 0;
        }
        if(suma_valor !== this.doc.amount){
            alert(`El pago debe ser ${this.doc.amount}`);
            this.reset_payment_button();
        }
        else{

        RM.working("Generating Invoice");
        this.order.data.dinners = this.dinners.val();
        //frappe.msgprint(this.order.data.electronic_invoice);
        //frappe.msgprint(this.electronic_invoice.val());
        frappeHelper.api.call({
            model: "Table Order",
            name: this.order.data.name,
            method: "make_invoice",
            args: {
                mode_of_payment: this.payments_values,
                customer: this.get_value("customer"),
                dinners: this.dinners.float_val,
                electronic_invoice: this.order.data.electronic_invoice
            },
            always: (r) => {
                RM.ready();
                
                if (r.message && r.message.status) {
                    order_manage.clear_current_order();
                    order_manage.check_buttons_status();
                    order_manage.check_item_editor_status();
                    
                    this.hide();

                    order_manage.make_orders();

                    // TIDAX
                    RM.working("Generating Invoice Electronic");
                    var com = frappe.defaults.get_user_default('company');

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
                filtro: "print_format_ce"
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
                filtro: "print_format_ce"
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
        let total_con_desc = 0;
        setTimeout(() => {
            Object.keys(this.payment_methods).forEach((payment_method) => {
                total += this.payment_methods[payment_method].float_val;
            });

            //TIDAX
            if(this.doc.discount > 0) {
                total_con_desc = this.order.amount - this.doc.discount
                this.set_value("amount", total_con_desc);
                this.set_value("total_payment", total);
                this.set_value("change_amount", (total - total_con_desc));
            }
            else if(this.doc.discount_global_percent > 0){
                total_con_desc = this.order.amount*(1-(this.doc.discount_global_percent/100));
                this.set_value("amount", total_con_desc);
                this.set_value("total_payment", total);
                this.set_value("change_amount", (total - total_con_desc));
            }
            else{
                this.set_value("total_payment", total);
                this.set_value("change_amount", (total - this.order.amount));
            }
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
