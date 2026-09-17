frappe.ui.form.on("PedidosYa Order", {
    refresh(frm) {
        if (frm.is_new()) return;
        if (frm.doc.status === "Awaiting Acceptance") {
            frm.add_custom_button(__("Accept Order"), () => {
                frappe.call({
                    method: "restaurant_management.integrations.pedidosya.service.accept_order",
                    args: { name: frm.doc.name },
                    freeze: true,
                    callback: () => frm.reload_doc(),
                });
            }).addClass("btn-primary");
            frm.add_custom_button(__("Reject Order"), () => {
                frappe.prompt(
                    [
                        {
                            fieldname: "reason",
                            fieldtype: "Select",
                            label: __("Reason"),
                            options: "ITEM_UNAVAILABLE\nMENU_ACCOUNT_SETTINGS\nTOO_BUSY\nCLOSED\nNO_COURIER\nNO_PICKER\nOUTSIDE_DELIVERY_AREA\nTECHNICAL_PROBLEM",
                            reqd: 1,
                        },
                        { fieldname: "message", fieldtype: "Small Text", label: __("Message") },
                    ],
                    (values) => frappe.call({
                        method: "restaurant_management.integrations.pedidosya.service.reject_order",
                        args: { name: frm.doc.name, reason: values.reason, message: values.message },
                        freeze: true,
                        callback: () => frm.reload_doc(),
                    }),
                    __("Reject PedidosYa Order")
                );
            });
        }
        if (["Error", "Review"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Retry Processing"), () => {
                frappe.call({
                    method: "restaurant_management.integrations.pedidosya.service.retry_order",
                    args: { name: frm.doc.name },
                    freeze: true,
                    callback: () => frm.reload_doc(),
                });
            });
        }
    },
});
