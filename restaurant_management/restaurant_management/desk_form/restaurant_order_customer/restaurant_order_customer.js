frappe.ready(function() {
	// bind events here
	// frappe.web_form.after_load = () => {
	// 	frappe.desk_form.on('customer', (field, value) => {
	// 		jug = value;
	// 		console.log(jug);
	// 		windows.print(jug);
	// 		clientes = obtener_cliente_por_filtro(jug);
	// 	});
	// }

	//  // Agregar la función para obtener clientes por filtro
	// function obtener_cliente_por_filtro(filtro) {
    //     // Obtener los clientes según el filtro especificado
    //     return frappe.call({
    //         method: "restaurant_management.restaurant_management.doctype.utils.obtener_cliente_por_filtro",
    //         args: {
    //             filtro: filtro
    //         },
    //         callback: function(r) {
    //             // Manejar la respuesta del servidor
    //             if (r.message) {
    //                 console.log(r.message[4]);
	// 				//frappe.desk_form.set_value('customer_tipo_documento_identidad', r.message[3])
	// 				frappe.web_form.set_value('customer_tipo_documento_identidad', "Paso")
    //             }
    //         }
    //     });
    // }
})