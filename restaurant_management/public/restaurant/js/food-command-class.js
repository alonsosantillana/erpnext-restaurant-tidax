class FoodCommand {
    constructor(options) {
        Object.assign(this, options);
        this.rendered = false;
        this.item = null;
        this.render();
        RM.object(this.identifier + this.process_manage.identifier, this);
    }
    render() {
        if (!this.rendered) {
            this.action_button = frappe.jshtml({
                tag: "h5",
                properties: {
                    class: `btn btn-default btn-flat btn-food-command`,
                    style: 'border-radius: 0 !important; font-size: 8px;'
                },
                content: '{{text}}<i class="fa fa-chevron-right pull-right" style="font-size: 14px; padding-top: 0px;"></i>',
                text: this.data.process_status_data.next_action_message,
            }).on("click", () => {
                this.execute();
            }, !RM.restrictions.to_change_status_order ? DOUBLE_CLICK : null)
            // TIDAX: QUITA PERMISO A MOZOS
            if (frappe.session.user.includes("mozo")) {
                this.action_button.prop('disabled', true);
            }

            this.status_label = frappe.jshtml({
                tag: "h5",
                properties: {
                    class: "btn btn-flat btn-food-command status-label",
                    style: `background-color: ${this.data.process_status_data.color}; font-size: 8px;`
                },
                content: `<i class="${this.data.process_status_data.icon} pull-left status-label-icon" style="font-size: 9px;"></i> ${this.data.process_status_data.status_message}`,
            });

            this._time_elapsed = frappe.jshtml({
                tag: "strong",
                properties: {
                    style: "font-size: 14px; left: 100%; position: sticky;"
                },
                content: ''
            });

            this.description = frappe.jshtml({
                tag: "span",
                properties: {
                    style: "text-align: text-top; font-size: 11px;"
                },
                content: `${this.data.table_description} | ${this.data.short_name}`,
            });

            this.title = frappe.jshtml({
                tag: "h5",
                content: `${this.description.html()} ${this._time_elapsed.html()}`,
            });
            
            this.item = frappe.jshtml({
                tag: "article",
                properties: {
                    class: "food-command-container"
                },
                content: this.template
            });
            //TIDAX: NO MOSTRAR EN PANTALLA DELIVERYS
            let cadena = this.data.table_description;
            let inicio = cadena.indexOf("(") + 1;
            let fin = cadena.indexOf(")");
            let resultado = cadena.substring(inicio, fin);
            let m1, m2, m3;
            //this.usarMesas(resultado);
            m1 = RM.restrictions.mesas_1;
            m2 = RM.restrictions.mesas_2;
            m3 = RM.restrictions.mesas_3;
            if(!resultado.includes(m1) && !resultado.includes(m2) && !resultado.includes(m3)){
            $(this.process_manage.command_container()).append(
                this.item.html()
            );}

            this.rendered = true;
            this.show_notes();

            this.time_elapsed;

        }
    }
    render1() {
        if (!this.rendered) {
            
            this.action_button = frappe.jshtml({
                tag: "h5",
                properties: {
                    class: `btn btn-default btn-flat btn-food-command`,
                    style: 'border-radius: 0 !important; font-size: 8px;'
                },
                content: '{{text}}<i class="fa fa-chevron-right pull-right" style="font-size: 14px; padding-top: 0px;"></i>',
                text: this.data.process_status_data.next_action_message,
            }).on("click", () => {
                this.execute();
            }, !RM.restrictions.to_change_status_order ? DOUBLE_CLICK : null)
            // TIDAX: QUITA PERMISO A MOZOS
            if (frappe.session.user.includes("mozo")) {
                this.action_button.prop('disabled', true);
            }

            this.status_label = frappe.jshtml({
                tag: "h5",
                properties: {
                    class: "btn btn-flat btn-food-command status-label",
                    style: `background-color: ${this.data.process_status_data.color}; font-size: 8px;`
                },
                content: `<i class="${this.data.process_status_data.icon} pull-left status-label-icon" style="font-size: 9px;"></i> ${this.data.process_status_data.status_message}`,
            });

            this._time_elapsed = frappe.jshtml({
                tag: "strong",
                properties: {
                    style: "font-size: 14px; left: 100%; position: sticky;"
                },
                content: ''
            });

            this.description = frappe.jshtml({
                tag: "span",
                properties: {
                    style: "text-align: text-top; font-size: 11px;"
                },
                content: `${this.data.table_description} | ${this.data.short_name}`,
            });

            this.title = frappe.jshtml({
                tag: "h5",
                content: `${this.description.html()} ${this._time_elapsed.html()}`,
            });
            
            this.item = frappe.jshtml({
                tag: "article",
                properties: {
                    class: "food-command-container"
                },
                content: this.template
            });
            //TIDAX: NO MOSTRAR EN PANTALLA DELIVERYS
            let cadena = this.data.table_description;
            let inicio = cadena.indexOf("(") + 1;
            let fin = cadena.indexOf(")");
            let resultado = cadena.substring(inicio, fin);
            let m1, m2, m3;
            //this.usarMesas(resultado);
            m1 = RM.restrictions.mesas_1;
            m2 = RM.restrictions.mesas_2;
            m3 = RM.restrictions.mesas_3;
            if(!resultado.includes(m1) && !resultado.includes(m2) && !resultado.includes(m3)){
            $(this.process_manage.command_container()).append(
                this.item.html()
            );}

            this.rendered = true;
            this.show_notes();

            this.time_elapsed;
        }
    }

    
    // TIDAX: COLOR ALEATORIO
    getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    // Método para actualizar lastShortName
    updateLastShortName() {
        this.lastShortName = this.data.short_name;
    }

    update_title() {
        this.description.val(this.data.table_description + " | " + this.data.short_name);
    }

    refresh_html() {
        const psd = this.data.process_status_data;
        this.update_title();
        this.detail.val(this.html_detail);
        this.action_button.val(psd.next_action_message);

        this.show_notes();

        this.status_label.val(
            `<i class="${psd.icon} pull-left" style="font-size: 16px"></i> ${psd.status_message}`
        ).css([
            { prop: "background-color", value: psd.color }
        ]);
    }

    execute() {
        if (RM.busy_message()) {
            return;
        }
        RM.working(this.data.next_action_message, false);
        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.process_manage.table.data.name,
            method: "set_status_command",
            args: {
                identifier: this.data.identifier,
                tiempo: this._time_elapsed.value
            },
            always: () => {
                RM.ready(false, "success");
            },
        });
    }

    // TIDAX: OBTENCION DE RESTRICCION DE MESAS
    obtenerMesas(mesas) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Restaurant Settings',
                    fieldname: mesas
                },
                callback: function (response) {
                    let xxx = mesas.substring(6, 7);
                    if (response && response.message) {
                        let yyy = response.message['mesas_' + xxx];
                        const mesas_1 = yyy;
                        resolve(mesas_1);
                    } else {
                        reject('No se pudo obtener el valor de mesas_1.');
                    }
                },
                error: function (err) {
                    reject('Error al obtener el valor de mesas_1:', err);
                }
            });
        });
    }

    async usarMesas(resultado) {
        try {
            const mesas_1 = await this.obtenerMesas("mesas_1");
            const mesas_2 = await this.obtenerMesas("mesas_2");
            const mesas_3 = await this.obtenerMesas("mesas_3");
            if (!resultado.includes(mesas_1) && !resultado.includes(mesas_2) && !resultado.includes(mesas_3)) {
                // Aquí puedes realizar cualquier lógica adicional
                $(this.process_manage.command_container()).append(
                    this.item.html()
                );
            }
        } catch (error) {
            console.error(error);
        }
    }

    remove() {
        this.item.remove();

        const items = Object.keys(this.process_manage.items);

        items.forEach((item) => {
            if (this.process_manage.items[item].data.identifier === this.data.identifier) {
                delete this.process_manage.items[item];
            }
        });
    }

    get html_detail_oficial() {
        return `
		<div class="row food-command-detail">
			<div style="width: 30%; display: inline-block">
				<h5 style="width: 100%; font-size: 50px">${this.data.qty}</h5>
			</div>
			<div style="width: 30%; display: inline-block">
				<h5 style="width: 100%">Rate</h5>
				<h6 style="width: 100%">${RM.format_currency(this.data.rate)}</h6>
			</div>
			<div style="width: 30%; display: inline-block">
				<h5 style="width: 100%">Total</h5>
				<h6 style="width: 100%">${RM.format_currency(this.data.amount)}</h6>
			</div>
		</div>
		`
    }

    get html_detail() {
        return `
        <div class="row food-command-detail">
            <div style="width: 10%; display: inline-block;">
                <h6 style="width: 100%; font-size: 18px;">${this.data.qty}</h6>
            </div>
            <div style="width: 70%; display: inline-block;">
                <h6 style="width: 100%;  font-size: 9px;"><b>${this.data.item_name}</b></h6>
            </div>
        </div>`;
    }

    get time_elapsed() {
        this._time_elapsed.val(RMHelper.prettyDate(this.data.ordered_time, true, time_elapsed => this.show_alert_time_elapsed(time_elapsed)));
    }

    show_alert_time_elapsed(time_elapsed) {
        const five_minuts = 60 * 5;
        const fifteen_minuts = 60 * 15;

        if (time_elapsed <= five_minuts) {
            this._time_elapsed.css('color', 'green');
        } else if (time_elapsed > five_minuts && time_elapsed <= fifteen_minuts) {
            this._time_elapsed.css('color', 'orange');
        } else if (time_elapsed > fifteen_minuts) {
            this._time_elapsed.css('color', 'red');
            this._time_elapsed.add_class('alert-time');
        }
    }

    get template() {
        this.detail = frappe.jshtml({
            tag: "div",
            properties: {
                class: "row food-command-detail"
            },
            content: this.html_detail
        });
        
        this.notes = frappe.jshtml({
            tag: "div",
            properties: { class: "row product-notes", style: "display: none;" },
            content: '<h6 style="width: 93%; font-size: 8px;"><center>{{text}}</center></h6>',
            text: ""
        });
        // TIDAX
        this.alerta_pedido = frappe.jshtml({
            tag: "audio controls ",
            // properties: { class: "row product-notes", style: "display: none;" },
            properties: { preload: "auto" },
            content: '<source src="/assets/frappe/sounds/submit.mp3" type="audio/mpeg">',
            text: ""
        });

        // return `			
		// <div class="food-command">
        //     <div style= "display: none;">${$("#sound-submit").trigger('play')}</div>
		// 	<div class="food-command-title">
        //     ${this.title.html()}
		// 	</div>
		// 	${this.detail.html()}
		// 	<div class="row" style="height: auto">
		// 		<h3 style="width: 100%">${this.data.item_name}</h3>
		// 	</div>
		// 	<div class="row" style="height: auto">
		// 	</div>
		// 	${this.notes.html()}
		// 	<div class="food-command-footer">
		// 		<div style="display: table-cell">
		// 			${this.status_label.html()}
		// 		</div>
		// 		<div style="display: table-cell">
		// 			${this.action_button.html()}
		// 		</div>
		// 	</div>
		// </div>`
        return `			
		<div class="food-command">
            <div style= "display: none;">${$("#sound-submit").trigger('play')}</div>
			<div class="food-command-title">
            ${this.title.html()}
			</div>
			${this.detail.html()}
			${this.notes.html()}
			<div class="food-command-footer">
				<div style="display: table-cell;">
					${this.status_label.html()}
				</div>
				<div style="display: table-cell;">
					${this.action_button.html()}
				</div>
			</div>
		</div>`
    }

    show_notes() {
        setTimeout(() => {
            if (this.notes.obj != null) {
                if (typeof this.data.notes == "object" || this.data.notes === "" || this.data.notes === "") {
                    this.notes.val(__("No annotations")).hide();
                } else {
                    this.notes.val(this.data.notes).show();
                }
            }
        }, 0);
    }
}