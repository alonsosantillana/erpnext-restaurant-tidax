class OrderManage extends ObjectManage {
    #objects = {};
    #components = {};
    #items = {};
    #numpad = null;
    orders_reloading = false;
    select_order_after_reload = false;

    constructor(options) {
        super(options);

        this.modal = null;
        this.print_modal = null;
        this.current_order = null;
        this.transferring_order = false;
        this.is_fulfillment = Boolean(this.external_order_data);
        this.table_name = this.table.data.name;
        this.order_container_name = `order-container-${this.table_name}`;
        this.order_entry_container_name = `container-order-entry-${this.table_name}`;
        this.editor_container_name = `edit-container-${this.table_name}`;
        this.pad_container_name = `pad-container-${this.table_name}`;
        this.item_container_name = `items-container-${this.table_name}`;
        this.invoice_container_name = `invoice-container-${this.table_name}`;
        this.not_selected_order = null;
        this.init_synchronize();
        this.initialize();
    }

    //get invoice_wrapper() { return document.getElementById(this.invoice_container_name);}
    get objects() { return this.#objects }
    get components() { return this.#components }
    get items() { return this.#items }
    get orders() { return super.children }
    get numpad() { return this.#numpad }

    get container() { return document.getElementById(this.identifier); }
    get order_container() { return document.getElementById(this.order_container_name); }
    get order_entry_container() { return document.getElementById(this.order_entry_container_name); }

    init_synchronize() {
        frappe.realtime.on("pos_profile_update", () => {
            setTimeout(() => {
                this.check_buttons_status();
            }, 0);
        });
    }

    reload() {
        if (!this.is_enabled_to_open()) return;
        this.modal.load_data();
    }

    initialize() {
        if (!this.is_enabled_to_open()) return;
        this.title = this.is_fulfillment
            ? this.table.data.description
            : this.table.room.data.description + " (" + this.table.data.description + ")";
        this.modal = RMHelper.default_full_modal(
            this.title,
            () => {
                this.make();
            }
        );
    }

    is_enabled_to_open() {
        if (this.is_fulfillment) {
            return RM.check_permissions("order", null, "read")
                || RM.check_permissions("order", null, "write")
                || RM.can_pay;
        }
        if (!RM.can_open_order_manage(this.table)) {
            this.close();
            return false;
        }
        return true;
    }

    show() {
        if (!this.is_enabled_to_open()) return;

        this.modal.show();
        if (this.container) {
            this.reload_orders_silently(true);
        } else {
            this.select_order_after_reload = true;
        }
        if (this.transferring_order) {
            if (this.current_order != null) {
                //**To move windows over the current, on transferring order**//
                this.current_order.edit_form = null;
                this.current_order.divide_account_modal = null;
                this.current_order.pay_form = null;
            }
            this.transferring_order = false;
        }
    }

    close() {
        this.modal.hide()
    }

    make() {
        this.make_dom();
        this.get_orders();
        this.make_items();
        this.make_edit_input();
        this.make_pad();

        if (this.transferring_order && this.current_order != null) {
            this.current_order.edit_form = null;
            this.current_order.divide_account_modal = null;
            this.current_order.pay_form = null;
            this.transferring_order = null;
        }
    }

    is_open() {
        return this.modal.modal.display
    }

    make_dom() {
        this.empty_carts = frappe.jshtml({
            tag: 'div',
            content: RMHelper.no_data('No added items'),
            properties: {
                class: 'empty-carts',
                /*style: 'display: none'*/
            }
        });

        this.not_selected_order = frappe.jshtml({
            tag: 'div',
            properties: { class: "no-order-message" },
            content: RMHelper.no_data('Select or create an Order')
        });

        this.modal.container.append(this.template());
        
        this.#components.change_mozo = RMHelper.default_button("Mozo", 'edit', () => this.update_current_order('mozo')); //TIDAX
        this.#components.customer = RMHelper.default_button("Customer", 'people', () => this.update_current_order('customer'));
        this.#components.new_customer = RMHelper.default_button("New Customer", 'addpeople', () => this.consultar_cliente()); //TIDAX
        this.#components.guest_count = RMHelper.default_button("Guest Count", 'peoples', () => this.update_current_order('guest_count'));
        this.#components.delete = RMHelper.default_button("Delete", 'trash', () => this.delete_current_order(), DOUBLE_CLICK);
        
        this.modal.title_container.empty().append(
            RMHelper.return_main_button(this.title, () => this.modal.hide()).html()
        )

        this.modal.buttons_container.prepend(`
			${this.components.delete.html()}
            ${this.components.change_mozo.html()} 
            ${this.components.new_customer.html()} 
            ${this.components.customer.html()}
			${this.components.guest_count.html()}
		`);

        if (this.is_fulfillment) {
            this.components.delete.hide();
            this.components.change_mozo.hide();
            this.components.new_customer.hide();
            this.components.customer.hide();
            this.components.guest_count.hide();
        }
    }

    template() {
        this.invoice_wrapper = frappe.jshtml({
            tag: 'div',
            properties: {
                id: this.invoice_container_name,
                class: 'product-list',
                style: "height: 100%;"
            },
        });

        this.items_wrapper = frappe.jshtml({
            tag: 'div',
            properties: {
                id: this.item_container_name,
                class: 'product-list',
                style: "height: 100%;"
            },
        });

        return `
		<div class="order-manage" id="${this.identifier}">
			<table class="layout-table">
				<tr class="content-row">
					<td>
						<div class="order-container" id="${this.order_container_name}"></div>
					</td>
					<td class="erp-items" style="width: 100%">
						<div class="content-container">
							${this.items_wrapper.html()}
                            ${this.invoice_wrapper.html()}
                            <div class="col-md-12">
							
							</div>
						</div>
					</td>
					<td class="container-order-items">
						<div class="panel-order-items">
							<ul class="products-list" id="${this.order_entry_container_name}">
								
							</ul>
							${this.empty_carts.html()}
							${this.not_selected_order.html()}
						</div>
						<table class="table no-border table-condensed panel-order-edit" id ="${this.editor_container_name}">
						
						</table>
						<table class="table no-border order-manage-control-buttons pad-container" id="${this.pad_container_name}">
						
						</table>
					</td>
				</tr>
			</table>
		</div>`
    }

    toggle_main_section(option="items"){
        if(option == "items"){
            this.items_wrapper.show();
            this.invoice_wrapper.hide();
        }else{
            this.items_wrapper.hide();
            this.invoice_wrapper.show();
        }
    }

    in_objects(f) {
        Object.keys(this.objects).forEach((key) => {
            f(this.objects[key])
        });
    }

    empty_inputs() {
        this.in_objects(obj => {
            if (["qty", "discount", "rate"].includes(obj.properties.name)) {
                obj.val("", false);
            }
        });
    }

    make_edit_input() {
        const default_class = `input entry-order-editor input-with-feedback center`;

        const objs = [
            {
                name: "Minus",
                tag: 'button',
                properties: {
                    name: 'minus', 
                    class: `btn btn-default edit-button ${default_class}` 
                },
                content: '<span class="fa fa-minus">',
                on: {
                    'click': () => {
                        this.adjust_quantity(-1);
                    }
                }
            },
            {
                name: "Qty",
                tag: 'button', label: 'Qty',
                properties: { 
                    name: 'qty', type: 'text', input_type: "number",
                    class: default_class
                },
                on: {
                    'click': (obj) => {
                        this.num_pad.input = obj;
                    }
                }
            },
            {
                name: "Discount",
                tag: 'button', label: 'Discount',
                properties: { 
                    name: 'discount', type: 'text', input_type: "number",
                    class: default_class,
                },
                on: {
                    'click': (obj) => {
                        this.num_pad.input = obj;
                    }
                }
            },
            {
                name: "Rate",
                tag: 'button', label: 'Rate',
                properties: { 
                    name: 'rate', type: 'text', input_type: "number",
                    class: default_class
                },
                on: {
                    'click': (obj) => {
                        this.num_pad.input = obj;
                    }
                }
            },
            {
                name: "Plus",
                tag: 'button',
                properties: {
                    name: 'plus',
                    class: `btn btn-default edit-button ${default_class}`
                },
                content: '<span class="fa fa-plus">',
                on: {
                    'click': () => {
                        this.adjust_quantity(1);
                    }
                }
            },
            {
                name: "Trash",
                tag: 'button',
                properties: {
                    name: 'trash',
                    class: `btn btn-default edit-button ${default_class}`,
                    title: __("Delete selected dish (press twice)"),
                    'aria-label': __("Delete selected dish (press twice)")
                },
                confirm_message: __("Press Delete again to remove the selected dish"),
                content: '<span class="fa fa-trash">',
                on: {
                    'click': () => {
                        const current_item = this.current_order ? this.current_order.current_item : null;
                        if (current_item != null) {
                            if (current_item.is_enabled_to_delete) {
                                current_item.delete();
                                // console.log(current_item.data.status);
                                // // TIDAX: CONDICION BORRADO PRODUCTO
                                // if (frappe.session.user.includes("mozo") && current_item.data.status == "Attending") {
                                //     current_item.delete();
                                // }
                                // if (frappe.session.user.includes("mozo") && current_item.data.status != "Attending") {
                                //     frappe.msgprint(__("El producto ya se envio a cocina. No tiene permisos para eliminar el producto en este estado."));
                                // }
                                // if (!frappe.session.user.includes("mozo")) {
                                //     current_item.delete();
                                // }

                            } else {
                                frappe.msgprint(__("You do not have permissions to delete Items"));
                            }
                        }
                    }
                }
            }
        ];

        const container = "#" + this.editor_container_name;
        let base_html = "<thead><tr>";
        const width = [10, 20, 20, 20, 10, 10];

        objs.forEach((_obj) => {
            base_html += `
			<th class="center pad-head" style="font-size: 12px; padding: 4px">
				${_obj.label || ""}
			</th>`
        });
        base_html += "</thead><tbody><tr class='edit-values'>";

        objs.forEach((element, index) => {
            base_html += `<td class='${this.table_name}-${index}' style='width: ${width[index]}%;'>`;

            this.#objects[element.name] = frappe.jshtml({
                tag: element.tag,
                properties: element.properties,
                content: (element.content || ""),
                confirm_message: element.confirm_message
            }).on(
                Object.keys(element.on)[0], element.on[Object.keys(element.on)[0]], (element.name === "Trash" ? DOUBLE_CLICK : "")
            ).disable();

            base_html += this.objects[element.name].html();
        });
        
        $(container).empty().append(base_html + "</tr></tbody>");

        this.#objects.Qty.int();
        this.#objects.Discount.float(2);
        this.#objects.Rate.float();
    }

    adjust_quantity(delta) {
        const input = this.objects.Qty;
        const can_queue_quantity = this.current_order
            && this.current_order.has_pending_item_mutations();
        if ((RM.busy && !can_queue_quantity) || !input || input.is_disabled) return;

        const current_value = flt(input.val());
        const value = Math.max(1, current_value + delta);

        if (value === current_value) {
            frappe.show_alert({
                message: __("Quantity must be at least 1. Use Delete to remove the item."),
                indicator: "orange"
            });
            return;
        }

        this.num_pad.input = input;
        input.val(value, false);
        this.update_detail(input);
        input.focus();
    }

    update_detail(input) {
        if (!input) return;

        const fieldname = input.properties.name;
        const can_queue_quantity = fieldname === "qty"
            && this.current_order
            && this.current_order.has_pending_item_mutations();
        if (RM.busy && !can_queue_quantity) return;

        const set_data = (item, qty, discount, rate, quantity_only = false) => {
            item.data.qty = qty;
            item.data.discount_percentage = discount;
            item.data.rate = rate;
            item.data.status = item.order.data.attending_status || "Attending";
            item.update(!quantity_only);
            if (quantity_only) {
                item.order.queue_item_quantity(item, qty);
            }
            if (qty > 0) {
                item.select();
            }
        }

        if (this.current_order != null && this.current_order.current_item != null) {
            const current_item = this.current_order.current_item;
            if (!current_item.is_enabled_to_edit) {
                return;
            }

            const qty = flt(this.objects.Qty.val());
            let discount = flt(this.objects.Discount.val());
            let rate = flt(this.objects.Rate.val());
            const base_rate = flt(current_item.data.price_list_rate);

            if (qty < 1) {
                this.objects.Qty.val(current_item.data.qty, false);
                frappe.show_alert({
                    message: __("Quantity must be at least 1. Use Delete to remove the item."),
                    indicator: "orange"
                });
                return;
            }

            discount = Math.min(100, Math.max(0, discount));
            rate = Math.max(0, rate);

            if (fieldname === "qty") {
                set_data(current_item, qty, discount, rate, true);
            }
            if (fieldname === "discount") {
                this.objects.Discount.val(discount, false);
                rate = (base_rate * (1 - discount / 100));
                this.objects.Rate.val(rate, false);
                set_data(current_item, qty, discount, rate);
            }
            if (fieldname === "rate") {
                this.objects.Rate.val(rate, false);
                const _discount = base_rate > 0 ? (((base_rate - rate) / base_rate) * 100) : 0;
                discount = _discount >= 0 ? _discount : 0
                this.objects.Discount.val(discount, false);
                set_data(current_item, qty, discount, rate);
            }
        }
    }

    make_pad() {
        const default_class = `pad-col ${this.table_name}`;
        this.orders_count_badge = frappe.jshtml({
            tag: 'span',
            properties: { class: 'badge badge-tag badge-btn', style: 'font-size: 12px' },
            content: "{{text}}",
            text: 0
        });

        const num_pads_components = [
            [
                [
                    {
                        name: "Pad",
                        props: { class: "", rowspan: 5, style: "width: 65% !important; padding: 0" },
                        action: "none"
                    },
                    {
                        name: "Order",
                        props: { class: "lg pad-btn btn-success btn-order" },
                        content: `<span class="fa fa-cutlery pull-right"></span>`,
                        action: "order"
                    }
                ]
            ],
            [
                [
                    {
                        name: "Account",
                        props: { class: "lg pad-btn" }, content: '<span class="fa fa-file-o pull-right"></span>',
                        action: "print_account_tdx"
                        //action: "print_account"
                    }
                ]
            ],
            [
                [
                    {
                        name: "Divide",
                        props: { class: "lg pad-btn" }, content: '<span class="fa fa-files-o pull-right"></span>',
                        action: "divide"
                    }
                ]
            ],
            [
                [
                    {
                        name: "Discount",
                        props: { class: "lg pad-btn" },
                        content: '<span class="fa fa-percent pull-right"></span>',
                        action: "set_discount"
                    }
                ]
            ],
            [
                [
                    {
                        name: "Transfer",
                        props: { class: "lg pad-btn" },
                        content: '<span class="fa fa-share pull-right"></span>',
                        action: "transfer"
                    }
                ]
            ],
            [
                [
                    {
                        name: "Tax",
                        props: { class: "pad-label lg", style: "padding-top: 3px;" }, action: "none"
                    },
                    {
                        name: "Pay",
                        props: { class: "md pay-btn text-lg btn-primary", rowspan: 2 }, action: "pay"
                    },
                ],
                {
                    style: "height: 10px;"
                }
            ],
            [
                [
                    {
                        name: "Total",
                        props: { class: "pad-label label-lg lg" }, action: "none"
                    }
                ],
                {
                    style: "height: 15px;"
                }
            ]
        ];

        let base_html = "<tbody>";
        num_pads_components.forEach((row) => {
            const props = typeof row[1] != "undefined" ? row[1] : {};
            base_html += `<tr style='${props.style || ""}'>`;

            row[0].forEach((col) => {
                col.props.class += ` ${default_class}-${col.name}`;
                this.#components[col.name] = frappe.jshtml({
                    tag: "td",
                    properties: col.props,
                    content: "{{text}}" + (col.content || ""),
                    text: __(col.name) + (["Tax", "Total"].includes(col.name) ? ": " + RM.format_currency(0) : "")
                }).on("click", () => {
                    if (col.action !== "none") {
                        if (this.current_order == null) {
                            this.no_order_message();
                            return;
                        }
                        if (col.action !== "order" && this.current_order.has_queue_items()) {
                            frappe.msgprint(__('Adding Items, please wait'));
                            return;
                        }
                        if (col.action === "order") {
                            frappe.show_alert({
                                message: __("Preparing order..."),
                                indicator: "blue"
                            });
                        }
                        setTimeout(() => {
                            const current_order = this.current_order;
                            const action = current_order && current_order[col.action];
                            if (typeof action !== "function") return;
                            try {
                                const result = action.call(current_order);
                                if (result && typeof result.catch === "function") {
                                    result.catch(error => this.handle_order_action_error(error));
                                }
                            } catch (error) {
                                this.handle_order_action_error(error);
                            }
                        }, 0);
                    }
                }, (col.action === "transfer" && !RM.restrictions.to_transfer_order ? DOUBLE_CLICK : null));

                base_html += this.components[col.name].html();
            });

            base_html += "</tr>";
        });
        $("#" + this.pad_container_name).empty().append(base_html + "</tbody>");

        setTimeout(() => {
            this.num_pad = new NumPad({
                wrapper: this.components.Pad.obj,
                replace_value_on_first_key: true,
                on_enter: () => {
                    if (this.num_pad.input && !this.num_pad.input.is_disabled) {
                        this.update_detail(this.num_pad.input);
                    }
                }
            });
            setTimeout(() => {
                this.check_buttons_status();
            }, 0);
        }, 0);
    }

    handle_order_action_error(error) {
        console.error("Restaurant order action failed", error);
        RM.ready();
        frappe.show_alert({
            message: __("The order operation could not be completed"),
            indicator: "red"
        });
    }

    is_same_order(order = null) {
        return this.current_order && order && this.current_order.data.name === order.data.name;
    }

    no_order_message() {
        frappe.msgprint("Not order Selected");
    }

    in_components(f) {
        Object.keys(this.components).forEach(k => {
            if (typeof this.#components[k] != "undefined") {
                f(this.components[k], k);
            }
        });
    }

    reset_order_button() {
        this.#components.Order.set_content(
            `<span class="fa fa-cutlery pull-right"></span>${__('Order')}{{text}}`
        ).reset_confirm();
    }

    refresh_discount_button() {
        const button = this.#components.Discount;
        if (!button) return;

        let detail = "";
        if (this.current_order) {
            const percent = flt(this.current_order.data.discount_global_percent);
            const amount = flt(this.current_order.data.discount);
            if (percent > 0) {
                detail = `: ${percent}%`;
            } else if (amount > 0) {
                detail = `: ${RM.format_currency(amount)}`;
            }
        }

        button.set_content(
            `<span class="fa fa-percent pull-right"></span>${__('Discount')}${detail}{{text}}`
        );
    }

    disable_components() {
        this.reset_order_button();
        this.in_components((component, k) => {
            if (!["Pad", "Tax", "Total"].includes(k)) {
                component.disable();

                if (["delete", "edit", "new", "new_order"].includes(k)) {
                    component.hide();
                }
            }
        });
    }

    check_buttons_status() {
        if (this.current_order == null) {
            this.disable_components();
            if (this.#components.new_order_button) {
                this.#components.new_order_button.enable().show();
            }
                
            return;
        } else {
            if (RM.check_permissions("order", null, "create")) {
                if (this.#components.new_order_button) {
                    this.#components.new_order_button.enable().show();
                }
            } else {
                if (this.#components.new_order_button) {
                    this.#components.new_order_button.disable().hide();
                }
            }
        }

        if (this.current_order.data.status !== "Invoiced") {
            if (this.current_order.items_count === 0) {
                if (RM.check_permissions("order", this.current_order, "delete")) {
                    this.#components.delete.enable().show();
                } else {
                    this.#components.delete.disable().hide();
                }
            } else {
                this.#components.delete.disable().hide();
                this.#components.Pay.prop("disabled", !RM.can_pay);
            }

            if (RM.check_permissions("order", this.current_order, "write")) {
                if (this.current_order.has_queue_items()) {
                    this.#components.Order.enable().add_class("btn-danger").val(__("Add"));
                } else {
                    const orders_count = this.current_order.data.products_not_ordered;
                    this.orders_count_badge.val(`${orders_count}`);
                    const [action, text] = [orders_count > 0 ? "enable" : "disable", orders_count > 0 ? this.orders_count_badge.html() : ""];

                    this.#components.Order.set_content(
                        `<span class="fa fa-cutlery pull-right"></span>${__('Order')}${text}{{text}}`
                    )[action]();
                }

                this.#components.Divide.prop("disabled", this.current_order.items_count === 0);
                this.#components.change_mozo.enable().show(); //TIDAX
                if (frappe.model.can_create("Customer")) {
                    this.#components.new_customer.enable().show(); //TIDAX
                } else {
                    this.#components.new_customer.disable().hide(); //TIDAX
                }
                this.#components.customer.enable().show();
                this.#components.guest_count.enable().show();
                this.#components.Discount.prop(
                    "disabled",
                    this.current_order.items_count === 0
                        || !Number(RM.pos_profile.allow_discount_change)
                );
                this.#components.Transfer.enable();
            } else {
                this.#components.new_customer.disable().hide(); //TIDAX
                this.#components.change_mozo.disable().hide(); //TIDAX
                this.#components.customer.disable().hide();
                this.#components.guest_count.disable().hide();
                this.#components.Discount.disable();
                this.#components.Transfer.disable();
                this.#components.Order.disable();
                this.#components.Divide.disable();
            }
        } else {
            this.disable_components();
        }

        if (this.is_fulfillment) {
            this.#components.delete.hide().disable();
            this.#components.change_mozo.hide().disable();
            this.#components.new_customer.hide().disable();
            this.#components.customer.hide().disable();
            this.#components.guest_count.hide().disable();
            this.#components.Divide.hide().disable();
            this.#components.Transfer.hide().disable();
        }

        this.#components.Account.prop(
            "disabled",
            !RM.check_permissions("order", this.current_order, "print") || this.current_order.items_count === 0
        );
        this.refresh_discount_button();
    }

    check_item_editor_status(item = null) {
        /** item OrderItem class **/
        const objects = this.#objects;
        if (item == null) {
            this.num_pad.input = null;
            this.empty_inputs();
            this.in_objects((input) => {
                input.disable();
            });
            return;
        }
        
        const pos_profile = RM.pos_profile
        const data = item.data;
        const item_is_enabled_to_edit = item.is_enabled_to_edit;

        objects.Qty.prop(
            "disabled", !item_is_enabled_to_edit
        ).val(data.qty, false);

        objects.Discount.prop(
            "disabled", !item_is_enabled_to_edit || !pos_profile.allow_discount_change
        ).val(data.discount_percentage, false);

        objects.Rate.prop(
            "disabled", !item_is_enabled_to_edit || !pos_profile.allow_rate_change
        ).val(data.rate, false);

        // Quantity is the safe default target for +/- and the numeric pad
        // whenever the operator selects another order line.
        this.num_pad.input = item_is_enabled_to_edit ? objects.Qty : null;

        objects.Minus.prop("disabled", !item_is_enabled_to_edit);
        objects.Plus.prop("disabled", !item_is_enabled_to_edit);
        // TIDAX: EL MOZO SOLO PUEDE ELIMINAR EN ESTADO ATENDIDO
        const is_cashier_or_admin = frappe.session.user === "Administrator"
            || frappe.session.user.includes("cajero")
            || frappe.session.user.includes("admin");
        const can_delete = item.is_enabled_to_delete && (
            this.is_fulfillment || is_cashier_or_admin || item.data.status === "Attending"
        );
        objects.Trash.prop("disabled", !can_delete);
        if (!this.is_fulfillment) {
            if (frappe.model.can_create("Customer")) {
                this.#components.new_customer.enable().show();
            }
            this.#components.change_mozo.enable().show();
        } else {
            this.#components.new_customer.hide().disable();
            this.#components.change_mozo.hide().disable();
        }
        
        item.check_status();
    }

    make_items() {
        //console.log(["make_items", this.items_wrapper]);
        this.#items = new ProductItem({
            wrapper: $(`#${this.item_container_name}`),
            order_manage: this,
        });
    }

    storage() {
        return this.#items;
    }

    add_order() {
        if (this.is_fulfillment) return;
        RM.working("Adding Order");
        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "add_order",
            args: { client: RM.client },
            callback: (r) => {
                if (!r.message) return;
                RM.request_client = r.message.client;
                this.check_data(r.message);
                RM.sound_submit();
            },
            always: () => {
                RM.ready();
            },
        });
    }

    get_orders(current = null) {
        RM.working(__("Loading Orders in") + ": " + this.title);
        if (current == null) current = this.current_order_identifier;
        if (this.is_fulfillment) {
            this.external_order_data = this.normalize_order_data(this.external_order_data);
            this.make_orders([this.external_order_data], current || this.external_order_data.data.name);
            RM.ready();
            return;
        }
        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "orders_list",
            args: {},
            always: (r) => {
                RM.ready();
                this.make_orders(r.message, current);
            },
        });
    }

    reload_orders_silently(select_if_empty = false) {
        this.select_order_after_reload = this.select_order_after_reload || select_if_empty;
        if (!this.container) return;
        if (this.is_fulfillment) {
            const active_order = this.current_order
                || (this.current_order_identifier
                    ? this.get_order(this.current_order_identifier)
                    : null);
            if (active_order && active_order.has_pending_order_mutations()) {
                clearTimeout(this.fulfillment_reload_timer);
                this.fulfillment_reload_timer = setTimeout(() => {
                    this.fulfillment_reload_timer = null;
                    this.reload_orders_silently(select_if_empty);
                }, 250);
                return;
            }
            if (this.orders_reloading) return;
            clearTimeout(this.fulfillment_reload_timer);
            this.fulfillment_reload_timer = null;
            this.orders_reloading = true;
            frappe.call({
                method: "restaurant_management.api.get_fulfillment_detail",
                args: { name: this.fulfillment_name },
                always: r => {
                    try {
                        if (r && r.message && r.message.order) {
                            const data = r.message.order;
                            data.order = this.normalize_order_data(data.order);
                            this.external_order_data = data.order;
                            const order = this.get_order(data.order.name);
                            if (order) {
                                order.reset_data(data, QUEUE);
                            } else {
                                this.append_order(data.order, data.order.name);
                            }
                        }
                    } catch (error) {
                        console.error("Delivery order reload failed", error);
                    } finally {
                        this.orders_reloading = false;
                    }
                }
            });
            return;
        }
        if (this.orders_reloading) return;
        this.orders_reloading = true;

        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "orders_list",
            args: {},
            always: (r) => {
                if (!r || r.exc || !Array.isArray(r.message)) {
                    this.orders_reloading = false;
                    return;
                }

                const persisted_orders = r.message;
                const persisted_names = new Set(persisted_orders.map(order => order.name));
                const stale_orders = [];
                const preferred_order_name = this.current_order
                    ? this.current_order.data.name
                    : (this.select_order_after_reload && persisted_orders.length > 0
                        ? persisted_orders[0].name
                        : null);

                this.in_orders(order => {
                    if (!persisted_names.has(order.data.name)) {
                        stale_orders.push(order.data.name);
                    }
                });
                stale_orders.forEach(order_name => this.delete_order(order_name));

                persisted_orders.forEach(order => {
                    let current = this.get_order(order.name);
                    if (current && !current.is_rendered) {
                        this.delete_order(order.name);
                        current = null;
                    }

                    if (current) {
                        current.data = Object.assign({}, order.data);
                        current.show_items_count();
                    } else {
                        this.append_order(order);
                    }
                });

                if (preferred_order_name && this.current_order == null) {
                    setTimeout(() => {
                        const order = this.get_order(preferred_order_name);
                        if (order && this.current_order == null) order.select();
                    });
                }

                this.select_order_after_reload = false;
                this.orders_reloading = false;
                this.check_permissions_status();
            },
            freeze: false,
        });
    }

    in_orders(f) {
        this.in_childs((child, key, index) => {
            f(child, key, index);
        })
    }

    check_permissions_status() {
        this.is_enabled_to_open();
        this.in_orders(order => {
            order.button.content = order.content;
            order.button.css(
                "color", RM.check_permissions('order', order, "write") ? "unset" : RM.restrictions.color
            ).val(order.data.items_count);
            if (this.is_same_order(order)) {
                this.check_buttons_status();
                this.check_item_editor_status(order.current_item);
            }
        });
    }

    check_data(data) {
        const _data = data.data.order.data;
        return super.append_child({
            child: _data,
            exist: o => {
                if ([UPDATE, QUEUE, SPLIT].includes(data.action)) {
                    o.reset_data(data.data, data.action);
                } else if ([DELETE, INVOICED, TRANSFER].includes(data.action)) {
                    this.delete_order(o.data.name);
                }
            },
            not_exist: () => {
                const new_order = new TableOrder({
                    order_manage: this,
                    data: Object.assign({}, _data)
                });

                if (RM.client === RM.request_client && new_order) {
                    setTimeout(() => {
                        new_order.select();
                    }, 0);
                }

                return new_order;
            }
        });
    }

    remove_transferred_order(order_name) {
        if (this.get_order(order_name) != null) {
            this.delete_order(order_name);
        }
    }

    receive_transferred_order(data) {
        this.check_data(Object.assign({}, data, { action: UPDATE }));
    }

    get_order(name) {
        return super.get_child(name);
    }

    make_orders(orders = [], current = null) {
        orders.forEach(order => {
            this.append_order(order, current);
        });
        
        if (this.#components.new_order_button){
            this.#components.new_order_button.remove();
        }

        if (this.is_fulfillment) {
            this.#components.new_order_button = null;
            return;
        }

        const new_order_button = frappe.jshtml({
            test_field:true,
            tag: "button",
            properties: {
                class: "btn btn-app btn-lg btn-order",
                style: 'background-color: var(--fill_color)'
            },
            content: `<span class="fa fa-plus"></span>`
        }).on("click", () => {
            this.add_order();
        }, !RM.restrictions.to_new_order ? DOUBLE_CLICK : null);

        this.#components.new_order_button = new_order_button;
        
        if (this.#components.new_order_button) {
            $(this.order_container).prepend(new_order_button.html());
        }
    }

    normalize_order_data(order) {
        if (!order || !order.data) return order;
        if (!order.name) order.name = order.data.name;
        return order;
    }

    append_order(order, current = null) {
        order = this.normalize_order_data(order);
        if (!order || !order.name) return null;
        return super.append_child({
            child: order,
            not_exist: () => {
                return new TableOrder({
                    order_manage: this,
                    data: Object.assign({}, order.data)
                });
            },
            always: o => {
                if (current != null && current === o.data.name) {
                    setTimeout(() => {
                        o.select();
                    }, 0);
                }
            }
        });
    }

    delete_current_order() {
        if (this.current_order != null) {
            this.current_order.delete();
        }
    }

    update_current_order(type) {
        if (this.current_order != null) {
            this.current_order.edit(type);
        }
    }
    // TIDAX
    consultar_cliente(){
        const order = this.current_order;
        if (!order) {
            frappe.show_alert({
                message: __("Select an order before creating a customer"),
                indicator: "orange"
            });
            return;
        }

        const escape_html = value => $("<div>").text(value || "").html();
        const dialog = new frappe.ui.Dialog({
            title: __("New Customer from DNI/RUC"),
            fields: [
                {
                    fieldname: "tax_id",
                    fieldtype: "Data",
                    label: __("DNI or RUC"),
                    description: __("Enter 8 digits for DNI or 11 digits for RUC"),
                    reqd: 1
                },
                {
                    fieldname: "customer_preview",
                    fieldtype: "HTML"
                }
            ]
        });
        const preview = dialog.fields_dict.customer_preview.$wrapper;

        const details_table = rows => `
            <table class="table table-bordered" style="margin: 10px 0 0;">
                <tbody>
                    ${rows.filter(row => row[1]).map(row => `
                        <tr>
                            <th style="width: 32%;">${escape_html(row[0])}</th>
                            <td>${escape_html(row[1])}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>`;

        const assign_customer = tax_id => {
            dialog.disable_primary_action();
            frappe.call({
                method: "restaurant_management.api.create_and_assign_customer",
                type: "POST",
                args: {
                    order_name: order.data.name,
                    tax_id: tax_id,
                    client: RM.client
                },
                freeze: true,
                freeze_message: __("Creating and assigning customer"),
                callback: r => {
                    if (!r.message) return;

                    order.reset_data(r.message.order, "Update");
                    dialog.hide();
                    frappe.show_alert({
                        message: r.message.created
                            ? __("Customer {0} created and assigned", [r.message.customer.customer_name])
                            : __("Customer {0} assigned", [r.message.customer.customer_name]),
                        indicator: "green"
                    });
                },
                always: () => dialog.enable_primary_action()
            });
        };

        const render_result = (result, tax_id) => {
            if (result.status === "existing") {
                const customer = result.customer;
                preview.html(`
                    <div class="alert alert-info" style="margin-top: 12px;">
                        <strong>${__("This customer already exists")}</strong>
                        ${details_table([
                            [__("Customer"), customer.customer_name],
                            [__("DNI or RUC"), customer.tax_id],
                            [__("Customer ID"), customer.name]
                        ])}
                    </div>`);
                dialog.set_primary_action(__("Use Customer"), () => assign_customer(tax_id));
                return;
            }

            if (result.status === "disabled") {
                preview.html(`
                    <div class="alert alert-warning" style="margin-top: 12px;">
                        <strong>${__("The customer registered with this document is disabled")}</strong>
                    </div>`);
                dialog.get_primary_btn().addClass("hide");
                return;
            }

            if (result.status === "not_found") {
                preview.html(`
                    <div class="alert alert-warning" style="margin-top: 12px;">
                        <strong>${__("No information was found for this DNI/RUC")}</strong>
                    </div>`);
                dialog.get_primary_btn().addClass("hide");
                return;
            }

            const identity = result.identity;
            const address = identity.registered_address || {};
            preview.html(`
                <div class="alert alert-success" style="margin-top: 12px;">
                    <strong>${__("Identity verified. Review the data before creating the customer.")}</strong>
                    ${details_table([
                        [__("Document Type"), identity.document_kind],
                        [__("DNI or RUC"), identity.tax_id],
                        [__("Customer Name"), identity.party_name],
                        [__("Customer Type"), identity.party_type],
                        [__("Registered Address"), address.address_line1],
                        [__("District"), address.district],
                        [__("Province"), address.province],
                        [__("Department"), address.department]
                    ])}
                </div>`);

            if (result.can_create) {
                dialog.set_primary_action(__("Create and Assign"), () => assign_customer(tax_id));
            } else {
                preview.append(`
                    <div class="alert alert-warning">
                        ${__("You do not have permission to create customers")}
                    </div>`);
                dialog.get_primary_btn().addClass("hide");
            }
        };

        const search_customer = () => {
            const tax_id = String(dialog.get_value("tax_id") || "").trim();
            if (!/^([0-9]{8}|[0-9]{11})$/.test(tax_id)) {
                frappe.msgprint(__("DNI must contain 8 digits and RUC must contain 11 digits"));
                return;
            }

            dialog.disable_primary_action();
            preview.html(`<p class="text-muted" style="margin-top: 12px;">${__("Searching DNI/RUC...")}</p>`);
            frappe.call({
                method: "restaurant_management.api.lookup_customer_identity",
                args: {tax_id: tax_id},
                freeze: true,
                freeze_message: __("Searching DNI/RUC"),
                callback: r => {
                    if (r.message) render_result(r.message, tax_id);
                },
                always: () => dialog.enable_primary_action()
            });
        };

        dialog.set_primary_action(__("Search"), search_customer);
        dialog.fields_dict.tax_id.$input.on("input", () => {
            preview.empty();
            dialog.set_primary_action(__("Search"), search_customer);
        });
        dialog.show();
        dialog.fields_dict.tax_id.set_focus();
    }

    clear_current_order() {
        this.#components.Tax.val(`${__("Tax")}: ${RM.format_currency(0)}`);
        this.#components.Total.val(`${__("Total")}: ${RM.format_currency(0)}`);
        this.check_item_editor_status();

        if (this.current_order != null) {
            this.delete_order(this.current_order.data.name);
        }
    }

    delete_order(order_name) {
        const order = this.get_order(order_name);
        if (order != null) {
            order.delete_items();
            if (this.is_same_order(order)) {
                this.current_order = null;
                this.clear_current_order();
            }
            super.delete_child(order_name);

            order.button.remove();
            order.container.remove();
            this.check_buttons_status();
            this.order_status_message();
        }
    }

    order_status_message() {
        const container = $("#" + this.identifier);
        
        if (this.current_order == null) {
            container.removeClass("has-order");
            container.removeClass("has-items");
        } else {
            container.addClass("has-order");
            if (this.current_order.items_count === 0) {
                container.removeClass("has-items");
            } else {
                container.addClass("has-items");
            }
        }
    }
}
