frappe.ui.form.on("Material Request", {
    refresh: function(frm, cdt, cdn){
		if(frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Resto"), function() {
				frm.events.get_items_from_pos_invoice(frm, cdt, cdn);
                //alert("LOGICA RESTO");
			}, __("Get Items From"));
			//frm.page.set_inner_btn_group_as_primary(__("Make"));
		}
	},

    get_items_from_pos_invoice: function(frm) {
		erpnext.utils.map_current_doc({
			method: "restaurant_management.restaurant_management.doctype.utils.make_material_request", //ANALIZAR
			source_doctype: "POS Invoice",
			target: frm,
			setters: {
				customer: frm.doc.customer || undefined,
				posting_date: undefined,
			},
			get_query_filters: {
				docstatus: 1,
				//status: ["not in", ["Closed", "On Hold"]],
				//per_delivered: ["<", 99.99],
				company: frm.doc.company
			}
		});
	},

	// clear_item_no_manufacturing: function(frm, cdt, cdn) {
	// 	// Obtén la lista de elementos de la tabla secundaria
	// 	const items = frm.doc.items || [];
	
	// 	// Inicializa una lista para almacenar los elementos que cumplen con la condición
	// 	const itemsCumplenCondicion = [];
	
	// 	// Contador para llevar un seguimiento de las llamadas a la API
	// 	let apiCallCounter = 0;
	
	// 	// Función para actualizar el formulario después de que se completen todas las llamadas a la API
	// 	function actualizarFormulario() {
	// 		// Actualiza el campo 'items' con los elementos que cumplen con la condición
	// 		frm.set_value('items', itemsCumplenCondicion);
	
	// 		// Recarga el formulario para reflejar los cambios
	// 		frm.refresh();
	// 	}
	
	// 	// Recorre los elementos de la tabla secundaria
	// 	for (let i = 0; i < items.length; i++) {
	// 		const item = items[i];
	
	// 		// Accede al campo 'item_code' en tu tabla secundaria
	// 		const itemCode = item.item_code;
	
	// 		// Realiza una llamada a la API de Frappe para obtener la información de la tabla maestra 'Items'
	// 		frappe.call({
	// 			method: "frappe.client.get",
	// 			args: {
	// 				doctype: "Item",
	// 				name: itemCode
	// 			},
	// 			callback: (r) => {
	// 				// Verifica si 'default_bom' no está vacío y guarda el registro si cumple con la condición
	// 				const defaultBom = r.message.default_bom;
	// 				if (defaultBom) {
	// 					itemsCumplenCondicion.push(item);
	// 				}
	
	// 				// Incrementa el contador de llamadas a la API
	// 				apiCallCounter++;
	
	// 				// Si se han completado todas las llamadas a la API, actualiza el formulario
	// 				if (apiCallCounter === items.length) {
	// 					actualizarFormulario();
	// 				}
	// 			}
	// 		});
	// 	}
	// },

	clear_item_no_manufacturing: function(frm, cdt, cdn) {
    // Obtén la lista de elementos de la tabla secundaria
    const items = frm.doc.items || [];

    // Inicializa un diccionario para almacenar la suma de 'qty' por 'item_code'
    const qtyPorItemCode = {};

    // Contador para llevar un seguimiento de las llamadas a la API
    let apiCallCounter = 0;

    // Función para actualizar el formulario después de que se completen todas las llamadas a la API
    function actualizarFormulario() {
        // Convierte el diccionario en una lista para actualizar el campo 'items'
        const itemsActualizados = Object.values(qtyPorItemCode);

        // Actualiza el campo 'items' con los elementos que cumplen con la condición y la suma de 'qty'
        frm.set_value('items', itemsActualizados);

        // Recarga el formulario para reflejar los cambios
        frm.refresh();
    }

    // Recorre los elementos de la tabla secundaria
    for (let i = 0; i < items.length; i++) {
        const item = items[i];

        // Accede al campo 'item_code' en tu tabla secundaria
        const itemCode = item.item_code;

        // Realiza una llamada a la API de Frappe para obtener la información de la tabla maestra 'Items'
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Item",
                name: itemCode
            },
            callback: (r) => {
                // Verifica si 'default_bom' no está vacío y guarda el registro si cumple con la condición
                const defaultBom = r.message.default_bom;
                if (defaultBom) {
                    // Verifica si ya existe una entrada para 'item_code' en el diccionario
                    if (qtyPorItemCode[itemCode]) {
                        // Si existe, suma 'qty' al valor existente
                        qtyPorItemCode[itemCode].qty += item.qty;
						qtyPorItemCode[itemCode].pos_invoice += "/" + item.pos_invoice;
						
                    } else {
                        // Si no existe, agrega una nueva entrada en el diccionario
                        qtyPorItemCode[itemCode] = { ...item };
						//qtyPorItemCode[itemCode].pos_invoice += item.pos_invoice;
                    }
                }

                // Incrementa el contador de llamadas a la API
                apiCallCounter++;

                // Si se han completado todas las llamadas a la API, actualiza el formulario
                if (apiCallCounter === items.length) {
                    actualizarFormulario();
                }
            }
        });
    }
},

});
