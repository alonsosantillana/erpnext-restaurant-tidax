(() => {
    const can_print = (frm) =>
        frm.doc.docstatus === 1 && frappe.model.can_print(null, frm);

    const request_id = () => {
        if (frappe.silent_print && frappe.silent_print.make_id) {
            return frappe.silent_print.make_id();
        }
        return `restaurant-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    };

    const queue_ticket = async (frm) => {
        if (frm.__restaurant_print_busy) return;
        frm.__restaurant_print_busy = true;

        try {
            const response = await frappe.call({
                method: "restaurant_management.printing.queue_invoice_print",
                type: "POST",
                args: {
                    invoice_name: frm.doc.name,
                    request_id: request_id(),
                },
                freeze: true,
                freeze_message: __("Enviando comprobante a la estación de impresión..."),
            });
            const result = response.message || {};
            if (!result.queued) {
                frappe.throw(__("No se pudo encolar el comprobante para impresión."));
            }
            if (!result.station_active) {
                frappe.msgprint({
                    title: __("Impresión en cola"),
                    message: __(
                        "El trabajo {0} quedó en espera. Abra la estación de impresión {1} en la caja para enviarlo a la ticketera.",
                        [result.job, result.station]
                    ),
                    indicator: "orange",
                    primary_action: {
                        label: __("Abrir estación"),
                        action: () => {
                            localStorage.removeItem("_page:restaurant-print-console");
                            window.open("/app/restaurant-print-console", "_blank");
                            frappe.hide_msgprint();
                        },
                    },
                });
                return;
            }
            frappe.show_alert({
                message: result.duplicate
                    ? __("Esta impresión ya estaba en cola: {0}", [result.job])
                    : __("Comprobante enviado a impresión: {0}", [result.job]),
                indicator: result.duplicate ? "orange" : "green",
            }, 7);
        } finally {
            frm.__restaurant_print_busy = false;
        }
    };

    const add_print_actions = (frm) => {
        if (!can_print(frm)) return;

        // Keep Frappe's standard PDF route as an explicit secondary action.
        frm.add_custom_button(__("Vista previa / PDF"), () => frm.print_doc());
        frm.add_custom_button(__("Imprimir"), () => queue_ticket(frm));
        frm.change_custom_button_type(__("Imprimir"), null, "primary");
    };

    frappe.ui.form.on("POS Invoice", {
        refresh(frm) {
            add_print_actions(frm);
        },
    });
})();
