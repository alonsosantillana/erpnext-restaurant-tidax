frappe.ui.form.on('Resto Gastos', 'validate', function(frm){
set_total_qty(frm);
});
frappe.ui.form.on('Resto Gastos Detalle', 'importe_gto', function(frm, cdt, cdn){
set_total_qty(frm);
});
//calcular cantidad de zapatos
var set_total_qty = function(frm){
    var total_qty = 0.0;
    $.each(frm.doc.gto_detalle, function(i, row){
        total_qty += flt(row.importe_gto);
    });
    frm.set_value('gto_total', total_qty);
    frm.doc.gto_total = total_qty;
    //frm.refresh();
};
