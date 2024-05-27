ProcessManage = class ProcessManage {
    constructor(options) {
        Object.assign(this, options);
        this.status = "close";
        this.modal = null;
        this.items = {};
        this.command_container_name = this.table.data.name + "-command_container";
        this.new_items_keys = [];

        this.initialize();
    }

    reload() {
        this.get_commands_food();
    }

    initialize() {
        this.title = this.table.room.data.description + " (" + this.table.data.description + ")";
        if (this.modal == null) {
            this.modal = RMHelper.default_full_modal(this.title, () => this.make());
        } else {
            this.show();
        }
    }

    show() {
        this.modal.show();
    }

    is_open() {
        return this.modal.modal.display;
    }

    close() {
        this.modal.hide();
        this.status = "close";
    }

    make() {
        this.make_dom();
        this.get_commands_food();
    }

    make_dom() {

        this.modal.container.empty().append(this.template());
        this.modal.title_container.empty().append(
            RMHelper.return_main_button(this.title, () => this.modal.hide()).html(),
            `<button id="openPopupButton" class="btn btn-default btn-flat">Consolidacion de Platos</button>`,
            `<button id="openPopupButtonCom" class="btn btn-default btn-flat">Comandas</button>`,
            `<button id="openPopupButtonAte" class="btn btn-default btn-flat">Pedidos Atendidos</button>`
        );
        if (frappe.session.user.includes("cocin") || frappe.session.user.includes("bar")) {
            this.agrupacion_platos();
            this.agrupacion_comandas();
            this.agrupacion_platos_atendidos();
        }
    }
    // TIDAX: Agrupa los platos pendientes y los muestra en una nueva ventana
    agrupacion_platos() {
        // Agrega un evento al botón "Abrir Nueva Ventana"
        document.getElementById('openPopupButton').addEventListener('click', () => {
            const popupWindow = window.open("", "Consolidacion de Platos", "width=850,height=500,top=100,left=100");
            //console.log(frappe.session.user);
            // Realiza una solicitud a la API de Frappe para obtener los elementos de la tabla hija
            frappe.call({
                method: "restaurant_management.restaurant_management.doctype.utils.get_ordenes_cocina_resumen",
                args: {
                    usuario: frappe.session.user
                },
                callback: (r) => {
                    const orderItems = r.message[0];
                    const orderItemsDelivery = r.message[1];
                    if (popupWindow && !popupWindow.closed) {
                        let cant = 0;
                        let cantDel = 0;
                        // Abre un documento HTML en la nueva ventana y muestra los datos
                        const popupDocument = popupWindow.document;
                        popupDocument.open();
                        popupDocument.write(`<html><head><title>Platos Consolidados</title></head><body>
                        <style>
                            * {
                            box-sizing: border-box;
                            }

                            /* Create three equal columns that floats next to each other */
                            .column {
                            float: left;
                            width: 50%;
                            padding: 10px;
                            /* height: 300px; Should be removed. Only for demonstration */
                            }

                            /* Clear floats after the columns */
                            .row:after {
                            content: "";
                            display: table;
                            clear: both;
                            }
                            </style>
                        `);
                        popupDocument.write("<h2>Consolidacion de Platos:</h2>");
                        popupDocument.write("<button type='button' style='border-radius: 8px; padding: 8px 20px;' id='refreshButton'>Actualizar</button>");
                        popupDocument.write("<div class= 'row'> <div class= 'column'>");
                        popupDocument.write(`<center><table id='tableData' style="border-radius: 40px; border: 1px solid #9c9c9c; padding: 15px;">`);
                        popupDocument.write("<tr><th>[Qty]</th><th>Nombre</th></tr>");
                        // popupDocument.write("<tr><th>[Qty]</th><th>Codigo</th><th>Nombre</th></tr>");
                        orderItems.forEach((item) => {
                                cant = cant + item.qty;
                                popupDocument.write("<tr>");
                                popupDocument.write("<td>[" + item.qty + "]</td>");
                                // popupDocument.write("<td>" + item.item_code + "</td>");
                                popupDocument.write("<td>" + item.item_name + "</td>");
                                popupDocument.write("</tr>");
                        });

                        popupDocument.write(`</table></center>`);
                        popupDocument.write(`<div id='totalqty'><center><b>Platos Totales: [${cant}]</b></center></div>`);

                        popupDocument.write(`</div><div class= 'column'>`);

                        popupDocument.write(`<center><table id='tableData1' style="border-radius: 40px; border: 1px solid #9c9c9c; padding: 15px; background: #e9e9e9;">`);
                        popupDocument.write("<tr><th>[Qty]</th><th>Nombre</th></tr>");
                        // popupDocument.write("<tr><th>[Qty]</th><th>Codigo</th><th>Nombre</th></tr>");
                        orderItemsDelivery.forEach((item) => {
                            cantDel = cantDel + item.qty;
                            popupDocument.write("<tr>");
                            popupDocument.write("<td>[" + item.qty + "]</td>");
                            // popupDocument.write("<td>" + item.item_code + "</td>");
                            popupDocument.write("<td>" + item.item_name + "</td>");
                            popupDocument.write("</tr>");
                        });

                        popupDocument.write(`</table></center>`);
                        popupDocument.write(`<div id='totalqty1'><center><b>Deliveries Totales: [${cantDel}]</b></center></div>`);
                        popupDocument.write("</div></div>");
                        // Agrega un evento al botón de actualización
                        const refreshButton = popupDocument.getElementById('refreshButton');
                        refreshButton.addEventListener('click', () => {
                            // Llama a la función para cargar y mostrar nuevamente los datos
                            refreshData();
                        });
                        // Función para cargar y mostrar los datos
                        function refreshData() {
                            cant = 0;
                            cantDel = 0;
                            // Realiza nuevamente la solicitud a la API de Frappe para obtener los elementos de la tabla hija
                            frappe.call({
                                method: "restaurant_management.restaurant_management.doctype.utils.get_ordenes_cocina_resumen",
                                args: {
                                    usuario: frappe.session.user
                                },
                                callback: (r) => {
                                    const orderItems = r.message[0];
                                    const orderItemsDelivery = r.message[1];

                                    // Encuentra la tabla y actualiza su contenido
                                    const tableData = popupDocument.getElementById('tableData');
                                    const totalqty = popupDocument.getElementById('totalqty');
                                    tableData.innerHTML = "<tr><th>[Qty]</th><th>Nombre</th></tr>";
                                    // tableData.innerHTML = "<tr><th>[Qty]</th><th>Codigo</th><th>Nombre</th></tr>";

                                    orderItems.forEach((item) => {
                                        cant = cant + item.qty;
                                        tableData.innerHTML += "<tr><td>[" + item.qty + "]</td>" + "<td>" + item.item_name + "</td></tr>";
                                        // tableData.innerHTML += "<tr><td>[" + item.qty + "]</td><td>" + item.item_code + "</td><td>" + item.item_name + "</td></tr>";
                                    });
                                    totalqty.innerHTML = `<center><b>Platos Totales: [${cant}]</b></center>`;

                                    // Encuentra la tabla y actualiza su contenido
                                    const tableData1 = popupDocument.getElementById('tableData1');
                                    const totalqty1 = popupDocument.getElementById('totalqty1');
                                    tableData1.innerHTML = "<tr><th>[Qty]</th><th>Nombre</th></tr>";
                                    // tableData.innerHTML = "<tr><th>[Qty]</th><th>Codigo</th><th>Nombre</th></tr>";

                                    orderItemsDelivery.forEach((item) => {
                                        cantDel = cantDel + item.qty;
                                        tableData1.innerHTML += "<tr><td>[" + item.qty + "]</td>" + "<td>" + item.item_name + "</td></tr>";
                                        // tableData.innerHTML += "<tr><td>[" + item.qty + "]</td><td>" + item.item_code + "</td><td>" + item.item_name + "</td></tr>";
                                    });
                                    totalqty1.innerHTML = `<center><b>Deliveries Totales: [${cantDel}]</b></center>`;

                                }
                            });
                        }
                        // Llama a la función de actualización automáticamente cada minuto
                        setInterval(refreshData, 60000); // 60000 milisegundos = 1 minuto


                        popupDocument.write("</body></html>");
                        popupDocument.close();
                    } else {
                        // Maneja el caso en el que la ventana emergente fue bloqueada
                        alert("La ventana emergente fue bloqueada. Por favor, habilita las ventanas emergentes en tu navegador.");
                    }
                }
            });
            // Cierra la ventana emergente después de 5 minutos
            // setTimeout(() => {
            //     popupWindow.close();
            // }, 5 * 60 * 1000); // 5 minutos en milisegundos
        });
    }

    // TIDAX: MUESTRA EN UNA NUEVA VENTANA LOS PLATOS ATENDIDOS DEL DIA
    agrupacion_platos_atendidos() {
        // Agrega un evento al botón "Abrir Nueva Ventana"
        document.getElementById('openPopupButtonAte').addEventListener('click', () => {
            const popupWindow = window.open("", "Platos Atendidos", "width=600,height=400,top=100,left=100");

            // Realiza una solicitud a la API de Frappe para obtener los elementos de la tabla hija
            frappe.call({
                method: "restaurant_management.restaurant_management.doctype.utils.get_ordenes_cocina_atendidos",
                args: {
                    usuario: frappe.session.user
                },
                callback: (r) => {
                    const orderItems = r.message;
                    const fecha = new Date();
                    if (popupWindow && !popupWindow.closed) {
                        let cant = 0;
                        // Abre un documento HTML en la nueva ventana y muestra los datos
                        const popupDocument = popupWindow.document;
                        popupDocument.open();
                        popupDocument.write("<html><head><title>Platos Atendidos</title></head><body>");
                        popupDocument.write(`<h2>Platos Atendidos(${fecha.toLocaleDateString()}):</h2>`);
                        popupDocument.write(`<center><table id='tableData' style="border-radius: 40px; border: 1px solid #9c9c9c; padding: 15px;">`);
                        popupDocument.write("<tr><th>[Qty]</th><th>Nombre</th></tr>");
                        orderItems.forEach((item) => {
                            cant = cant + item.qty;
                            popupDocument.write("<tr>");
                            popupDocument.write("<td>[" + item.qty + "]</td>");
                            // popupDocument.write("<td>" + item.item_code + "</td>");
                            popupDocument.write("<td>" + item.item_name + "</td>");
                            popupDocument.write("</tr>");
                        });
                        popupDocument.write(`</table></center>`);
                        popupDocument.write(`<div id='totalqty'><center><b>Platos Totales: [${cant}]</b></center></div>`);
                        popupDocument.write("<button type='button' style='border-radius: 8px; padding: 8px 20px;' id='refreshButtonAte'>Actualizar</button>");
                        // Agrega un evento al botón de actualización
                        const refreshButton = popupDocument.getElementById('refreshButtonAte');
                        refreshButton.addEventListener('click', () => {
                            // Llama a la función para cargar y mostrar nuevamente los datos
                            refreshData();
                        });
                        // Función para cargar y mostrar los datos
                        function refreshData() {
                            cant = 0;
                            // Realiza nuevamente la solicitud a la API de Frappe para obtener los elementos de la tabla hija
                            frappe.call({
                                method: "restaurant_management.restaurant_management.doctype.utils.get_ordenes_cocina_atendidos",
                                args: {
                                    usuario: frappe.session.user
                                },
                                callback: (r) => {
                                    const orderItems = r.message;

                                    // Encuentra la tabla y actualiza su contenido
                                    const tableData = popupDocument.getElementById('tableData');
                                    const totalqty = popupDocument.getElementById('totalqty');
                                    tableData.innerHTML = "<tr><th>[Qty]</th><th>Nombre</th></tr>";

                                    orderItems.forEach((item) => {
                                        cant = cant + item.qty;
                                        tableData.innerHTML += "<tr><td>[" + item.qty + "]</td>" + "<td>" + item.item_name + "</td></tr>";
                                        // tableData.innerHTML += "<tr><td>[" + item.qty + "]</td><td>" + item.item_code + "</td><td>" + item.item_name + "</td></tr>";
                                    });
                                    totalqty.innerHTML = `<center><b>Platos Totales: [${cant}]</b></center>`;
                                }
                            });
                        }
                        // Llama a la función de actualización automáticamente cada minuto
                        //setInterval(refreshData, 60000); // 60000 milisegundos = 1 minuto

                        popupDocument.write("</body></html>");
                        popupDocument.close();
                    } else {
                        // Maneja el caso en el que la ventana emergente fue bloqueada
                        alert("La ventana emergente fue bloqueada. Por favor, habilita las ventanas emergentes en tu navegador.");
                    }
                }
            });
        });
    }

    // TIDAX: MUESTRA EN UNA NUEVA VENTANA LAS COMANDAS POR ATENDER
    agrupacion_comandas() {
        // Agrega un evento al botón "Abrir Nueva Ventana"
        document.getElementById('openPopupButtonCom').addEventListener('click', () => {
            const popupWindow = window.open("", "Informacion Comandas", "width=900,height=600,top=100,left=100");
            // Realiza una solicitud a la API de Frappe para obtener los elementos de la tabla hija
            frappe.call({
                method: "restaurant_management.restaurant_management.doctype.utils.get_ordenes_cocina_comandas",
                args: {
                    usuario: frappe.session.user
                },
                callback: (r) => {
                    const ordenes = r.message;
                    //console.log(ordenes);
                    if (popupWindow && !popupWindow.closed) {
                        const popupDocument = popupWindow.document;
                        popupDocument.open();
                        // Mantener esta parte inalterada
                        popupDocument.write(`<html><head><title>Comandas</title>
                        <link rel="stylesheet" type="text/css" href="restaurant_management/restaurant_management/public/restaurant/css/cocina.css"></head>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">
                        
                        <body>`);
                        popupDocument.write('<button id="refreshButtonCom" class="btn btn-outline-secondary">Sincronizar Comandas</button>');
                        popupDocument.write('<span id="syncMessage" style="margin-left: 10px; color: green;"></span>'); // Nuevo elemento para mostrar el mensaje
                        popupDocument.write("<h3>Información de Comandas</h3>");
                        // Crea botones por cada grupo
                        const subNamesUnicos = [...new Set(ordenes.map(orden => orden.sub_name))];
                        const numeroDeGrupos = Math.ceil(subNamesUnicos.length / 4);
                        popupDocument.write('<div id="pagination" align = "center">');
                        for (let i = 0; i < numeroDeGrupos; i++) {
                            const buttonText = `Grupo ${i + 1}`;
                            popupDocument.write(`<button id="botonAgrupacion${i}" class="btn btn-outline-success">${buttonText}</button>`);
                        }
                        popupDocument.write(`<button id="refreshButtonCom1" class="btn btn-outline-success">Todo</button>`);
                        popupDocument.write('</div>');
                        // Agrega evento a los botones de agrupación
                        for (let i = 0; i < numeroDeGrupos; i++) {
                            const botonAgrupacion = popupDocument.getElementById(`botonAgrupacion${i}`);
                            botonAgrupacion.addEventListener('click', () => {
                                mostrarPedidos2(i + 1, subNamesUnicos.length, ordenes);
                            });
                        }
    
                        let compara = "";
                        let compara_ant = "";
    
                        // Itera sobre las órdenes y muestra la cabecera una vez y los detalles debajo de la misma en divs
                        popupDocument.write(`<div id="divData" style="justify-content: space-around; display: flex; flex-wrap: wrap;">`);
                        ordenes.forEach((orden, index) => {
                            if(!orden.table_description.includes("D")){
                            if ((orden.room_description + orden.table_description + orden.sub_name) !== compara) {
                                compara_ant = compara;
                                if (compara === compara_ant && compara_ant !== "") {
                                    popupDocument.write("</div>");
                                }
                                popupDocument.write(`<div id="tableData" style='line-height: 95%; float: left; position: relative;font-size: 0.8em; width: 20%; margin: 1% 0.5em;padding: 1% 0.5em; 
                                box-shadow: 0.1em 0.1em 0.2em #888888; box-sizing: border-box;border: 1px solid #9c9c9c; min-width: 20%; max-width: 20%;'>`);
                                popupDocument.write(`<button style='border-radius: 8px; padding: 8px 20px; width: 100%' id='comandaAtendido'>${orden.sub_name}</button>`);
                                popupDocument.write("<p>Sala: " + orden.room_description + " - Mesa: " + orden.table_description + " - Mozo: " + orden.owner);
                                popupDocument.write("<br>" + orden.comentario + "</p>");
                                compara = orden.room_description + orden.table_description + orden.sub_name;
                            }
                            if ((orden.room_description + orden.table_description + orden.sub_name) === compara) {
                                // popupDocument.write("<p><strong>[" + orden.qty + "]</strong>" +" "+orden.item_code+" "+ orden.item_name +"</p>");
                                popupDocument.write("<strong>[" + orden.qty + "]</strong>" + " " + orden.item_name + "<br>");
                                if (orden.notes) {
                                    popupDocument.write("<strong style='font-size: 0.8em; color: red'>N:" + orden.notes + "</strong><br>");
                                }
                            }}
                        });


                        const mostrarPedidos2 = (numeroDeGrupo, subNamesUnicos, ordenes) => {
                            // Obtén el elemento que contiene la información
                            const tableData = popupDocument.getElementById('divData');
                        
                            // Limpiar el contenido actual
                            tableData.innerHTML = '';

                            const syncMessage = popupDocument.getElementById('syncMessage');
                            syncMessage.innerText = `Grupo ${numeroDeGrupo}`;
                        
                            // Agrupa las órdenes por sub_name
                            const ordenesAgrupadas = agruparPorSubName(ordenes);
                        
                            // Calcula el rango de pedidos a mostrar en función del grupo
                            let inicio = (numeroDeGrupo - 1) * 4;
                            let fin = Math.min(numeroDeGrupo * 4, subNamesUnicos);
                        
                            for (let i = inicio; i < fin && i < ordenesAgrupadas.length; i++) {
                                const grupo = ordenesAgrupadas[i];

                                if(!grupo[0].table_description.includes("D")){
                        
                                // Muestra la cabecera solo si es diferente de la anterior
                                const cuadro = `<div  style='line-height: 95%; float: left; position: relative;font-size: 0.8em; width: 20%; margin: 1% 0.5em;padding: 1% 0.5em; 
                                    box-shadow: 0.1em 0.1em 0.2em #888888; box-sizing: border-box;border: 1px solid #9c9c9c; min-width: 20%; max-width: 20%;'>`;
                                //const boton = `<button style='border-radius: 8px; padding: 8px 20px; width: 100%' id='comandaAtendido'>${grupo[0].sub_name}</button>`;
                                const boton = `<button style='border-radius: 8px; padding: 8px 20px; width: 100%; background-color: #008CBA;' class='comandaAtendido' 
                                            data-order-name='${grupo[0].name}' data-ordered-time='${grupo[0].ordered_time}'>${grupo[0].sub_name}</button>`


                                const cabecera = "<p>Sala: " + grupo[0].room_description + " - Mesa: " + grupo[0].table_description +" - Mozo: " + grupo[0].owner + "<br>" + grupo[0].comentario +"</p>";
                        
                                // Muestra los detalles de la orden
                                const detalles = grupo.map(orden => "<strong>[" + orden.qty + "]</strong>" + " " + orden.item_name + "<br>").join('');
                        
                                const pie = grupo.map(orden => orden.notes ? "<strong style='font-size: 0.8em; color: red'>N:" + orden.notes + "</strong><br>" : '').join('');
                        
                                // Concatena las partes y agrega al contenedor
                                tableData.innerHTML += cuadro + boton + cabecera + detalles + pie + "</div>";
                                }
                            }

                            // Agrega eventos a los botones "Atendido"
                            const atendidoButtons = popupDocument.getElementsByClassName('comandaAtendido');
                            for (let i = 0; i < atendidoButtons.length; i++) {
                                atendidoButtons[i].addEventListener('click', (event) => {
                                    // Obtiene los valores de los atributos de datos del botón clickeado
                                    const orderName = event.target.dataset.orderName;
                                    const orderedTime = event.target.dataset.orderedTime;
                                    saveComanda(orderName, orderedTime);
                                });
                            }
                            // Función para guardar la comanda
                            const saveComanda = (orderName, orderedTime) => {
                                // Realiza una solicitud a la API de Frappe para actualizar la columna "status" de la tabla hija "Order Entry Item"
                                frappe.call({
                                    method: "restaurant_management.restaurant_management.doctype.utils.update_comanda_atendida",
                                    args: {
                                        order_name: orderName, // Nombre de la orden
                                        ordered_time: orderedTime, // Hora de la orden
                                        usuario: frappe.session.user
                                    },
                                    callback: (r) => {
                                        // Maneja la respuesta de la actualización (puedes mostrar un mensaje de éxito o realizar otras acciones necesarias)
                                        //alert("La orden ha sido marcada como 'Atendida'.");
                                        refreshData();
                                        this.reload();
                                    }
                                });
                            }
                        }

                        // Función para agrupar las órdenes por sub_name
                        const agruparPorSubName = (ordenes) => {
                            const ordenesAgrupadas = [];
                            const subNamesUnicos = [...new Set(ordenes.map(orden => orden.sub_name))];
                            subNamesUnicos.forEach(subName => {
                                const grupo = ordenes.filter(orden => orden.sub_name === subName);
                                ordenesAgrupadas.push(grupo);
                            });
                            return ordenesAgrupadas;
                        };                        
                        
                        // Agrega un evento al botón de actualización
                        const refreshButton = popupDocument.getElementById('refreshButtonCom');
                        refreshButton.addEventListener('click', () => {
                            // Llama a la función para cargar y mostrar nuevamente los datos
                            refreshData();

                            // Muestra el mensaje "Comandas sincronizadas"
                            const syncMessage = popupDocument.getElementById('syncMessage');
                            syncMessage.innerText = 'Comandas sincronizadas';

                            // Oculta el mensaje después de 3 segundos (ajusta el tiempo según tus necesidades)
                            setTimeout(() => {
                                syncMessage.innerText = '';
                            }, 3000);
                        });

                        // Agrega un evento al botón de actualización - Todo
                        const refreshButton1 = popupDocument.getElementById('refreshButtonCom1');
                        refreshButton1.addEventListener('click', () => {
                            // Llama a la función para cargar y mostrar nuevamente los datos
                            refreshData();

                            // Muestra el mensaje "Comandas sincronizadas"
                            const syncMessage = popupDocument.getElementById('syncMessage');
                            syncMessage.innerText = 'Comandas sincronizadas';

                            // Oculta el mensaje después de 3 segundos (ajusta el tiempo según tus necesidades)
                            setTimeout(() => {
                                syncMessage.innerText = '';
                            }, 3000);
                        });

                        // Función para cargar y mostrar los datos
                        const refreshData = () => {
                            // Realiza nuevamente la solicitud a la API de Frappe para obtener los elementos de la tabla hija
                            frappe.call({
                                method: "restaurant_management.restaurant_management.doctype.utils.get_ordenes_cocina_comandas",
                                args: {
                                    usuario: frappe.session.user
                                },
                                callback: (r) => {
                                    const ordenes = r.message;
                                    //if (popupWindow && !popupWindow.closed) {
                                    //const popupDocument = popupWindow.document;
                                    let compara = "";
                                    let cabecera = ""; // Almacena la cabecera actual
                                    let detalles = ""; // Almacena los detalles actuales
                                    let pie = "";

                                    let botones = "";

                                    // Obtén el elemento que contiene la información
                                    const tableData = popupDocument.getElementById('divData');
                                    const tableData1 = popupDocument.getElementById('pagination');

                                    // Limpiar el contenido actual
                                    tableData.innerHTML = '';
                                    tableData1.innerHTML = '';



                                    // Crea botones por cada grupo
                                    const subNamesUnicos = [...new Set(ordenes.map(orden => orden.sub_name))];
                                    const numeroDeGrupos = Math.ceil(subNamesUnicos.length / 4);

                                    for (let i = 0; i < numeroDeGrupos; i++) {
                                        const buttonText = `Grupo ${i + 1}`;
                                        botones += `<button id="botonAgrupacion${i}" class="btn btn-outline-success" >${buttonText}</button>`;
                                    }
                                    botones += `<button id="refreshButtonCom1" class="btn btn-outline-success">Todo</button>`;
                                    tableData1.innerHTML += botones;
                                    // Agrega evento a los botones de agrupación
                                    for (let i = 0; i < numeroDeGrupos; i++) {
                                        const botonAgrupacionxxx = popupDocument.getElementById(`botonAgrupacion${i}`);
                                        botonAgrupacionxxx.addEventListener('click', () => {
                                            mostrarPedidos2(i + 1, subNamesUnicos.length, ordenes);
                                        });
                                    }

                                    // Agrega un evento al botón de actualización - Todo
                                    const refreshButton1 = popupDocument.getElementById('refreshButtonCom1');
                                    refreshButton1.addEventListener('click', () => {
                                        // Llama a la función para cargar y mostrar nuevamente los datos
                                        refreshData();

                                        // Muestra el mensaje "Comandas sincronizadas"
                                        const syncMessage = popupDocument.getElementById('syncMessage');
                                        syncMessage.innerText = 'Comandas sincronizadas';

                                        // Oculta el mensaje después de 3 segundos (ajusta el tiempo según tus necesidades)
                                        setTimeout(() => {
                                            syncMessage.innerText = '';
                                        }, 3000);
                                    });

                                    // Itera sobre las órdenes y muestra la información formateada
                                    ordenes.forEach((orden) => {
                                        if(!orden.table_description.includes("D")){
                                        if ((orden.room_description + orden.table_description + orden.sub_name) !== compara) {
                                            if (compara) {
                                                // Si hay una cabecera previa, agrega el contenido
                                                tableData.innerHTML += cabecera + detalles + pie;
                                            }

                                            // Inicia una nueva cabecera
                                            cabecera = `<div style='line-height: 95%; float: left; position: relative;font-size: 0.8em; width: 20%; margin: 1% 0.5em;padding: 1% 0.5em; 
    box-shadow: 0.1em 0.1em 0.2em #888888; box-sizing: border-box;border: 1px solid #9c9c9c; min-width: 20%; max-width: 20%;'>
    <button style='border-radius: 8px; padding: 8px 20px; width: 100%; background-color: #008CBA;' class='comandaAtendido' 
    data-order-name='${orden.name}' data-ordered-time='${orden.ordered_time}'>${orden.sub_name}</button>
    <p>Sala: ${orden.room_description} - Mesa: ${orden.table_description} - Mozo: ${orden.owner} <br> ${orden.comentario}</p>`;
                                            detalles = ""; // Inicia una nueva sección de detalles
                                            compara = orden.room_description + orden.table_description + orden.sub_name;
                                        }

                                        // detalles += `<p><strong>[${orden.qty}]</strong> ${orden.item_code} ${orden.item_name}</p>`;
                                        detalles += `<strong>[${orden.qty}]</strong> ${orden.item_name}</br>`;
                                        if (orden.notes) {
                                            detalles += "<strong style='font-size: 0.8em; color: red'>N:" + orden.notes + "</strong><br>";
                                        }
                                    }});

                                    // Agrega el último conjunto de cabecera, detalles y pie
                                    if (compara) {
                                        tableData.innerHTML += cabecera + detalles + pie;
                                    }

                                    // Agrega eventos a los botones "Atendido"
                                    const atendidoButtons = popupDocument.getElementsByClassName('comandaAtendido');
                                    for (let i = 0; i < atendidoButtons.length; i++) {
                                        atendidoButtons[i].addEventListener('click', (event) => {
                                            // Obtiene los valores de los atributos de datos del botón clickeado
                                            const orderName = event.target.dataset.orderName;
                                            //console.log(orderName);
                                            const orderedTime = event.target.dataset.orderedTime;
                                            //console.log(orderedTime);
                                            saveComanda(orderName, orderedTime);
                                        });
                                    }
                                    // Función para guardar la comanda
                                    const saveComanda = (orderName, orderedTime) => {
                                        // Realiza una solicitud a la API de Frappe para actualizar la columna "status" de la tabla hija "Order Entry Item"
                                        frappe.call({
                                            method: "restaurant_management.restaurant_management.doctype.utils.update_comanda_atendida",
                                            args: {
                                                order_name: orderName, // Nombre de la orden
                                                ordered_time: orderedTime, // Hora de la orden
                                                usuario: frappe.session.user
                                            },
                                            callback: (r) => {
                                                // Maneja la respuesta de la actualización (puedes mostrar un mensaje de éxito o realizar otras acciones necesarias)
                                                //alert("La orden ha sido marcada como 'Atendida'.");
                                                refreshData();
                                                this.reload();
                                            }
                                        });
                                    }
                                    //} else {
                                    //alert("La ventana emergente fue bloqueada. Por favor, habilita las ventanas emergentes en tu navegador.");
                                    //}

                                }
                            });
                        }
                        // Llama a la función de actualización automáticamente cada minuto
                        // setInterval(refreshData, 18000); // 60000 milisegundos = 1 minuto

                        //popupDocument.write("</div></body></html>");
                        popupDocument.write("</body></html>");
                        popupDocument.close();
                    } else {
                        // Maneja el caso en el que la ventana emergente fue bloqueada
                        //alert("La ventana emergente fue bloqueada. Por favor, habilita las ventanas emergentes en tu navegador.");
                    }
                }
            });
            // Cierra la ventana emergente después de 5 minutos
            setTimeout(() => {
                popupWindow.close();
            }, 5 * 60 * 1000); // 5 minutos en milisegundos
        });
    }





    template() {
        return `
		<div class=" process-manage">
			<div id="${this.command_container_name}"></div>
		</div>`;
    }

    get_commands_food() {
        RM.working("Load commands food");
        frappeHelper.api.call({
            model: "Restaurant Object",
            name: this.table.data.name,
            method: "commands_food",
            args: {},
            always: (r) => {
                RM.ready();
                this.make_food_commands(r.message);
            },
        });
    }

    make_food_commands(items = []) {
        const _items = Object.keys(this.items);
        this.new_items_keys = [];

        items.forEach((item) => {
            this.new_items_keys.push(item.identifier);

            if (_items.includes(item.identifier)) {
                this.items[item.identifier].data = item;
            } else {
                this.add_item(item);
            }

            this.items[item.identifier].process_manage = this;
        });

        setTimeout(() => {
            this.debug_items();
        }, 100);

        this.time_elapsed();
    }

    time_elapsed() {
        setInterval(() => {
            this.in_items(item => {
                item.time_elapsed
            });
        }, 1000);
    }

    in_items(f) {
        Object.keys(this.items).forEach(k => {
            f(this.items[k]);
        })
    }

    check_items(items) {
        items.forEach((item) => {
            this.check_item(item);
        });
    }

    check_item(item) {
        if (Object.keys(this.items).includes(item.identifier)) {
            const _item = this.items[item.identifier];
            if (this.include_status(item.status)) {
                _item.data = item;
                _item.refresh_html();
            } else {
                _item.remove();
            }
        } else {
            if (this.include_status(item.status) && this.include_item_group(item.item_group)) {
                this.new_items_keys.push(item.identifier);
                this.add_item(item);
            }
        }
    }

    debug_items() {
        Object.keys(this.items).filter(x => !this.new_items_keys.includes(x)).forEach((r) => {
            this.items[r].remove();
        });
    }

    remove_item(item) {
        if (this.items[item]) {
            this.items[item].remove();
        }
    }

    add_item(item) {
        this.items[item.identifier] = new FoodCommand({
            identifier: item.identifier,
            process_manage: this,
            data: item
        });
    }

    include_status(status) {
        return this.table.data.status_managed.includes(status);
    }

    include_item_group(item_group) {
        return this.table.data.items_group.includes(item_group);
    }

    container() {
        return $(`#orders-${this.table.data.name}`);
    }

    command_container() {
        return document.getElementById(this.command_container_name);
    }
}