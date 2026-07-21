class OrderItem {
    enabled_form_fields_status = {
        "Pending": ["qty", "rate", "discount_percentage", "notes", "batch_no", "serial_no"],
        "Attending": ["qty", "rate", "discount_percentage", "notes", "batch_no", "serial_no"],
        "Sent": ["notes"],
        "Processing": ["notes"]
    }

    constructor(options) {
        Object.assign(this, options);

        this.attending_status = this.order.data.attending_status;
        this.status_enabled_for_edit = [this.attending_status, "Pending", null, undefined, ""];
        this.status_enabled_for_delete = [this.attending_status, "Pending", "Sent", null, undefined, ""];

        this.render();
        this.init_synchronize();
    }

    init_synchronize() {
        frappe.realtime.on("pos_profile_update", () => {
            setTimeout(() => {
                this.active_editor();
            }, 0);
        });
    }

    hide() {
        this.row.hide();
    }

    get is_enabled_to_edit() {
        return (this.status_enabled_for_edit.includes(this.data.status)) &&
            RM.check_permissions("order", this.order, "write");
    }

    get is_enabled_to_delete() {
        return (
            this.status_enabled_for_delete.includes(this.data.status)) &&
            (
                RM.check_permissions("order", this.order, "write")// &&
                //RM.check_permissions("pos", null, "delete")
        );
    }

    get pending_status_message() {
        return [this.attending_status, "Pending", null, undefined, ""].includes(this.data.status)
            ? __("Pending to send")
            : "";
    }

    reset_html() {
        const ps = this.data.process_status_data;
        const pending_status_message = this.pending_status_message;

        this.amount.val(RM.format_currency(this.data.amount));
        this.detail.val(this.html_detail);
        this.notes.val(this.data.notes);
        this.icon.val(`<i class="${ps.icon}" style="color: ${ps.color}"></i>`);
        this.status_label.val(pending_status_message)[pending_status_message ? "show" : "hide"]();

        this.form_editor && this.form_editor.reload(this.data, false);
    }

    delete() {
        if (RM.busy_message() || !this.is_enabled_to_delete) return;
        this.data.qty = 0;
        this.update(true);
    }

    remove() {
        this.row.remove();
    }

    render() {
        this.row = frappe.jshtml({
            tag: "li",
            properties: { class: "media event" },
            content: this.template
        });

        this.order.container.append(this.row.html());
    }

    async select(scroller = false) {
        this.order.current_item = this;
        this.order.order_manage.check_item_editor_status(this);
        this.row.toggle_common('media.event', 'selected');
        //this.order.order_manage.toggle_main_section("items");

        if (scroller) this.order.scroller();
    }

    active_editor() {
        if (typeof this.order == "undefined") return;
        this.order.order_manage.check_item_editor_status(this);
    }

    update(server = true) {
        if (this.edit_item) return;
        const deleting = this.data.qty === 0;
        if (this.data.qty === 0 && !this.is_enabled_to_delete) {
            frappe.throw(__("You do not have permissions to delete Items"));
        }

        if (this.data.qty === 0) {
            //this.order.delete_item(this.data.identifier);
        } else {
            this.calculate();
            this.reset_html();
        }

        this.order.aggregate(true);
        if (!server) return;
        this.order.queue_item_mutation(this, deleting);
    }

    calculate() {
        const base_amount = flt(this.data.qty) * flt(this.data.rate);
        this.tax_calculate(base_amount);

        this.order.order_manage.objects.Qty.val(this.data.qty);
        this.order.order_manage.objects.Rate.val(this.data.rate);
        this.order.order_manage.objects.Discount.val(this.data.discount_percentage);

        this.order.aggregate(true);
    }

    calculate_form(input, value) {
        //console.log("calculate_form", input)
        /**TODO: merge with general order management function */
        const set_data = (qty, discount, rate) => {
            this.data.qty = qty;
            this.data.discount_percentage = discount;
            this.data.rate = rate;
        }

        if (input && ["qty", "rate", "discount_percentage"].includes(input)) {
            //const input_field = this.form_editor.get_field(input);
            if (!this.is_enabled_to_edit) {
                return;
            }

            const qty_field = this.form_editor.get_field("qty");
            const rate_field = this.form_editor.get_field("rate");
            const discount_field = this.form_editor.get_field("discount_percentage");

            const qty = flt(qty_field.get_value());
            let discount = Math.min(100, Math.max(0, flt(discount_field.get_value())));
            let rate = flt(rate_field.get_value());
            const base_rate = flt(this.data.price_list_rate);

            if (input === "qty") {
                if (value === 0 && this.is_enabled_to_delete) {
                    frappe.msgprint(__("You do not have permissions to delete Items"));
                    return;
                }
                set_data(qty, discount, rate);
            }

            if (input === "discount_percentage") {
                rate = (base_rate * (1 - discount / 100));
                set_data(qty, discount, rate);
            }

            if (input === "rate") {
                const _discount = (((base_rate - rate) / base_rate) * 100);
                discount = _discount >= 0 ? _discount : 0
                set_data(qty, discount, rate);
            }
        } else {
            this.data[input] = value;
        }
        /**merge with general order management function */
    }

    tax_calculate(base_amount) {
        const tax_inclusive = RM.pos_profile.posa_tax_inclusive;

        const tax_amount = Object.values(RMHelper.JSONparse(this.data.item_tax_rate) || {}).reduce((acc, cur) => {
            if (tax_inclusive) {
                const base_without_tax = base_amount / (1 + (cur / 100));
                return acc + (base_without_tax * (cur / 100));
            } else {
                return acc + (base_amount * cur / 100);
            }
        }, 0);

        this.data.tax_amount = tax_amount;
        this.data.amount = base_amount + (tax_inclusive ? 0 : tax_amount);
    }

    discount_calculate(base_amount) {
        const discount_amount = flt(this.data.discount_amount);
        const discount_percentage = flt(this.data.discount_percentage);
        const tax_amount = flt(this.data.tax_amount);

        if (discount_amount > 0) {
            this.data.amount = base_amount + tax_amount - discount_amount;
        } else if (discount_percentage > 0) {
            this.data.discount_amount = base_amount * (discount_percentage / 100);
            this.data.amount = base_amount + tax_amount - this.data.discount_amount;
        } else {
            this.data.amount = base_amount + tax_amount;
        }
    }

    get template() {
        const psd = this.data.process_status_data;

        this.icon = frappe.jshtml({
            tag: "a",
            properties: { class: "pull-left border-aero profile_thumb" },
            content: `<i class="${psd.icon}" style="color: ${psd.color}"></i>`
        });

        this.notes = frappe.jshtml({
            tag: "small",
            properties: { class: "notes" },
            content: (typeof this.data.notes == "object" ? "" : this.data.notes)
        });

        this.status_label = frappe.jshtml({
            tag: "small",
            properties: { class: "order-item-status" },
            content: this.pending_status_message
        });

        this.detail = frappe.jshtml({
            tag: "p",
            content: this.html_detail
        });

        this.amount = frappe.jshtml({
            tag: 'a',
            properties: { class: 'pull-right' },
            content: RM.format_currency(this.data.amount)
        });

        this.form_editor_container = frappe.jshtml({
            tag: "div",
            properties: { class: "form-editor p-2" }
        });

        const header_template = `
        ${this.icon.html()}
        <div class="media-body">
            <a class="title" href="javascript:void(0)">${this.data.item_name}
                ${this.amount.html()}
            </a>
            ${this.detail.html()}
            ${this.status_label.html()}
            <p class="text-muted m-0">  ${this.notes.html()}</p>
        </div>
        `

        this.header = frappe.jshtml({
            tag: "div",
            properties: { class: "widget-user-header" },
            content: header_template
        }).on("click", async () => {
            RM.pull_alert("left");
            await this.make_form_editor();
            await this.select();
        });

        return `
        <div class="card card-widget widget-user-2">
            ${this.header.html()}
            <div class="card-footer p-0">
                ${this.form_editor_container.html()}
            </div>
        </div>
        `
    }

    async make_form_editor() {
        if (this.form_editor) {
            const selected = this.row.has_class("selected");
            await this.form_editor.reload(this.data);

            this.form_editor[!selected || this.form_editor.in_modal ? "show" : "toggle"]();
        } else {
            this.form_editor = new OrderItemEditor({
                order_item: this,
                location: this.form_editor_container.JQ(),
                doc: this.data,
                field_properties: {
                    item_code: {
                        read_only: true
                    },
                    has_batch_no: {
                        read_only: true,
                        hidden: this.data.has_batch_no === 0,
                    },
                    batch_no: {
                        hidden: this.data.has_batch_no === 0,
                        "get_query": () => {
                            return {
                                filters: [
                                    ['item', '=', this.data.item_code],
                                    ['disabled', '=', 0],
                                    ['batch_qty', '>', 0]
                                ]
                            }
                        }
                    },
                    has_serial_no: {
                        read_only: true,
                        hidden: this.data.has_serial_no === 0,
                    },
                    serial_no: {
                        hidden: this.data.has_serial_no === 0,
                        "get_query": () => {
                            return {
                                filters: [
                                    ['item_code', '=', this.data.item_code],
                                    ['status', '=', 'Active']
                                ]
                            }
                        }
                    },
                }
            });
            await this.form_editor.ready;
        }
    }

    check_status() {
        if (this.form_editor) {
            const fields = this.form_editor.get_fields();

            Object.entries(fields).forEach(([field_name, field]) => {
                const enabled = (this.enabled_form_fields_status[this.data.status] || []).includes(field_name);

                this.form_editor.set_field_property(field_name, "read_only", !enabled);
            });

            const pos_profile = RM.pos_profile;

            this.form_editor.set_field_property("qty", "read_only", !this.is_enabled_to_edit);
            this.form_editor.set_field_property("discount_percentage", "read_only", !this.is_enabled_to_edit || !pos_profile.allow_discount_change);
            this.form_editor.set_field_property("rate", "read_only", !this.is_enabled_to_edit || !pos_profile.allow_rate_change);
        }
    }

    get html_detail() {
        const rate = flt(this.data.rate, 2);
        const discount_percentage = flt(this.data.discount_percentage, RM.currency_precision);

        const discount_info = discount_percentage ? `
			<small class="badge" style="background-color: var(--dark); color: var(--green); padding:5px; display: inline;">
				<label>${discount_percentage}%<span class="fa fa-tags" style="padding-left: 5px;"></span></label>
			</small>` : ''

        return `${this.data.qty} x @${RM.format_currency(rate)} ${discount_info}`;
    }
}

class OrderItemEditor extends DeskForm {
    reload_from_doc = true;
    primary_action_label = __("Update");
    title = __("Item Editor");
    desk_form = RM.order_item_editor_form;
    disabled_to_save = true;

    constructor(opts) {
        super(opts);

        this.order_item = opts.order_item;
        // Frappe mutates DocField properties while refreshing controls. Each
        // dish therefore needs an isolated copy so another editor cannot leave
        // Notes or Discount Percentage in a read-only state.
        this.desk_form = JSON.parse(JSON.stringify(RM.order_item_editor_form));
        this.desk_form.desk_form_fields.forEach(df => {
            if (!df.fieldname) return;
            df.get_status = control => {
                if (cint(control.df.hidden) || cint(control.df.hidden_due_to_dependency)) {
                    return "None";
                }
                return cint(control.df.read_only) || control.df.fieldtype === "Read Only"
                    ? "Read"
                    : "Write";
            };
        });
        this.ready = super.initialize();
    }

    async make() {
        await super.make();

        const update = (field, input_value) => {
            const fieldname = field.df.fieldname;
            const value = typeof input_value === "undefined" ? field.get_value() : input_value;
            const current_value = this.order_item.data[fieldname];
            const unchanged = ["qty", "rate", "discount_percentage"].includes(fieldname)
                ? flt(current_value) === flt(value)
                : String(current_value || "") === String(value || "");
            if (unchanged) return;

            this.order_item.calculate_form(fieldname, value);
            this.order_item.calculate();
            this.order_item.update();
        }

        this.on(["qty", "rate", "batch_no"], "change", (field) => {
            update(field);
        });

        this.get_input("notes").css("height", "100px");
        this.save_details_button = $("<button>", {
            type: "button",
            class: "btn btn-primary btn-sm"
        }).append($("<span>", { class: "fa fa-save" }), " ", __("Save changes"));
        this.body.append(
            $("<div>", { class: "order-item-editor-actions" }).append(this.save_details_button)
        );
        this.save_details_button.on("click", () => this.save_visible_details());
    }

    save_visible_details() {
        if (this.saving_details) return;

        const notes_field = this.get_field("notes");
        const discount_field = this.get_field("discount_percentage");
        const notes = notes_field && notes_field.$input
            ? notes_field.$input.val()
            : notes_field.get_value();
        const discount_percentage = flt(
            discount_field && discount_field.$input
                ? discount_field.$input.val()
                : discount_field.get_value()
        );

        if (discount_percentage < 0 || discount_percentage > 100) {
            frappe.show_alert({
                message: __("Line discount percent must be between 0 and 100"),
                indicator: "orange"
            });
            return;
        }

        this.saving_details = true;
        this.save_details_button.prop("disabled", true);
        RM.working("Saving dish details", false);

        frappeHelper.api.call({
            model: "Table Order",
            name: this.order_item.order.data.name,
            method: "update_item_details",
            args: {
                identifier: this.order_item.data.identifier,
                notes,
                discount_percentage,
                client: RM.client
            },
            always: response => {
                const failed = !response || response.exc || !response.message;
                if (!failed) {
                    this.order_item.order.order_manage.check_data(response.message);
                    frappe.show_alert({
                        message: __("Dish details saved"),
                        indicator: "green"
                    });
                }
                this.saving_details = false;
                this.save_details_button.prop("disabled", false);
                RM.ready();
            }
        });
    }

    on_refresh_dependency() {
        this.order_item.check_status();
    }
}
