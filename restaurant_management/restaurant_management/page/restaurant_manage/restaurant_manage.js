/**RestaurantManagement**/
var RM = null;
const [TRANSFER, UPDATE, DELETE, INVOICED, ADD, QUEUE, SPLIT] = ["Transfer", "Update", "Delete", "Invoiced", "Add", "queue", "Split"];
frappe.provide('erpnext.PointOfSale');

frappe.pages['restaurant-manage'].on_page_load = async function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: '',
		single_column: true
	});

	const $page = $(wrapper).find('.layout-main-section');
	try {
		const bootstrap = await frappe.xcall(
			"restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.get_bootstrap"
		);
		RM = new RestaurantManage(wrapper);
		RM.bootstrap = bootstrap;
	} catch (error) {
		const message = error?.message || __("Restaurant Manage could not be initialized");
		$page.empty().append(
			$("<div>").addClass("alert alert-danger").text(message)
		);
		frappe.show_alert({ message, indicator: "red" });
	}
};
RestaurantManage = class RestaurantManage {
	#pos_profile = null;
	#permissions = null;
	#exceptions = null;
	#restrictions = null;
	#company = null;
	#components = [];
	#lang = null;
	currency_precision = 2;
	editing = false;
	transfer_order = null;
	current_room = null;
	busy = false;
	sounds = false;
	client =  this.uuid();
	request_client = null;
	loaded = false;
	table_reconciliation_interval = null;
	store = {
		items: []
	}
	objects = [];

	room = [];

	constructor(wrapper) {
		this.base_wrapper = wrapper;
		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;
		this.url_manage = "restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage.";
		this.#company = frappe.defaults.get_user_default('company');

		const assets = [
			'js/pos-restaurant-controller.js',
			'js/restaurant-room-class.js',
			'js/restaurant-object-class.js',

			'js/order-manage-class.js',
			'js/product-item-class.js',
			'js/order-item-class.js',

			'js/process-manage-class.js',
			'js/food-command-class.js',
			'js/table-order-class.js',
			'js/pay-form-class.js',
			'js/invoice-class.js',
			'js/fulfillment-board-class.js',

			'css/restaurant-room.css',
			'css/fulfillment-board.css',
			'css/action-buttons.css',
			'css/editor-order.css',
			'css/food-command.css',
			'css/order-buttons.css',
			'css/order-items.css',
			'css/order-items-container.css',
			'css/order-manage.css',
			'css/pay-form.css',
			'css/process-manage.css',
			'css/product-list.css',
			'css/restaurant-object.css',
			'css/cocina.css'
		].map(asset => `assets/restaurant_management/restaurant/${asset}`);

		frappe.require(assets, () => {
			this.make();
		});
	}

	make() {
		return frappe.run_serially([
			() => frappe.dom.freeze(),
			() => this.prepare_dom(),
			() => {
				this.working("Set settings");
				this.settings_data.then(() => {
					this.pos = new erpnext.PointOfSale.RestaurantController(this.wrapper);
					window.cur_pos = this.pos;

					this.make_rooms().then(() => {
						setTimeout(() => {
							this.check_permissions_status();
						}, 100);
					});
				});
			},
			() => {
				frappe.dom.unfreeze();
			},
			() => this.page.set_title(__('Restaurant Manage')),
			() => this.init_synchronize(),
			() => this.page.$title_area.hide()
		]);
	}

	test_pos() {
		if (this.loaded && this.pos_profile == null) {
			this.raise_exception_for_pos_profile();
		}
	}

	raise_exception_for_pos_profile() {
		if ($(this.base_wrapper).is(":visible")) {
			frappe.throw(this.not_has_pos_profile_message);
		}
	}

	get not_has_pos_profile_message() {
		return __("POS Profile is required to use Point-of-Sale");
	}

	prepare_dom() {
		const self = this;
		this.rooms_container = frappe.jshtml({
			tag: "div",
			properties: {
				style: "display: flex; width: 100%"
			}
		});

		this.floor_map = frappe.jshtml({
			tag: "div", properties: { class: "table-container-scroll" }
		}).on("click", () => {
			RM.unselect_all_tables();
		});

		this.fulfillment_hub_host = frappe.jshtml({
			tag: "div",
			properties: { class: "fulfillment-hub-host hide" }
		});

		this.fulfillment_board_host = frappe.jshtml({
			tag: "div",
			properties: { class: "fulfillment-board-host hide" }
		});

		this.#components.add_table = frappe.jshtml({
			tag: "button", properties: { class: "btn btn-default btn-flat" },
			content: `<span class="fa fa-plus"></span> ${__("Table")}`
		}).on("click", () => {
			this.add_object("Table");
		});

		this.#components.add_production_center = frappe.jshtml({
			tag: "button", properties: { class: "btn btn-default btn-flat" },
			content: `<span class="fa fa-plus"></span> ${__("P Center")}`
		}).on("click", () => {
			this.add_object("Production Center");
		});

		this.#components.edit_room = frappe.jshtml({
			tag: "button",
			properties: { class: "btn btn-default btn-flat" },
			content: `<span class="fa fa-pencil"></span> ${__("Edit")}`
		}).on("click", () => {
			if (this.current_room != null) this.current_room.edit();
		});

		this.#components.delete_room = frappe.jshtml({
			tag: "button",
			properties: { class: "btn btn-default btn-flat" },
			content: `<span class="fa fa-trash"></span> {{text}}`,
			text: __('Delete')
		}).on("click", () => {
			if (this.current_room != null) this.current_room.delete();
		}, DOUBLE_CLICK);

		this.general_edit_button = frappe.jshtml({
			tag: "div",
			properties: {
				class: 'btn-default button general-editor-button'
			},
			content: `<span class="fa fa-pencil"></span>`
		}).on("click", () => {
			this.set_edit_status();
		});

		this.add_room_button = frappe.jshtml({
			tag: "div",
			properties: {
				class: 'btn-default button general-editor-button add-room'
			},
			content: `<span class="fa fa-plus"></span>`
		}).on("click", () => {
			this.add_object("Room");
		});

		this.setting_button = frappe.jshtml({
			tag: "div",
			properties: {
				class: `btn-default button general-editor-button setting`,
				style: 'display: none'
			},
			content: '<span class="fa fa-gears"></span>'
		}).on("click", () => {

		});

		this.close_pos_button = frappe.jshtml({
			tag: "a",
			content: ' (' + __('Close') + ' <span class="fa fa-sign-out"></span>)'
		}).on("click", () => {
			frappe.confirm(
				'Close the POS?',
				function () {
					self.close_pos();
				},
			);
		});

		this.pos_profile_description = frappe.jshtml({
			tag: "span",
			properties: {
				class: 'pos-profile'
			},
			content: '{{text}}' + this.close_pos_button.html(),
			text: 'POS Profile'
		}).on("click", () => {
			frappe.confirm(
				'Close the POS?',
				function () {
					self.close_pos();
				},
			);
		});

		this.transfer_notice_text = frappe.jshtml({
			tag: "span",
			properties: { class: "transfer-notice-text" },
			content: "{{text}}",
			text: ""
		});

		this.cancel_transfer_button = frappe.jshtml({
			tag: "button",
			properties: { class: "btn btn-sm btn-warning transfer-cancel-button" },
			content: `<span class="fa fa-times"></span> ${__("Cancel transfer")}`
		}).on("click", () => this.cancel_order_transfer());

		this.transfer_notice = frappe.jshtml({
			tag: "div",
			properties: {
				class: "transfer-notice hide",
				role: "alert",
				"aria-live": "assertive"
			},
			content: `
				<div class="transfer-notice-message">
					<span class="fa fa-exchange transfer-notice-icon"></span>
					${this.transfer_notice_text.html()}
				</div>
				${this.cancel_transfer_button.html()}
			`
		});

		this.wrapper.append(`
			<div class="restaurant-manage">
				<div class="floor-selector">
					${this.general_edit_button.html()}
					${this.rooms_container.html()}
					${this.add_room_button.html()}
					${this.setting_button.html()}
				</div>
				${this.transfer_notice.html()}
				<div class="floor-map">
					<div class="floor-map-editor left">
						${this.components.add_table.html()}
						${this.components.add_production_center.html()}
					</div>
					<div class="floor-map-editor right">
						${this.components.edit_room.html()}
						${this.components.delete_room.html()}
					</div>
					<div class="restaurant-empty-rooms hide">
						<span class="fa fa-object-group restaurant-empty-rooms-icon"></span>
						<div class="restaurant-empty-rooms-title">${__("No rooms configured")}</div>
						<div class="restaurant-empty-rooms-help"></div>
						<button class="btn btn-primary restaurant-empty-rooms-create">
							<span class="fa fa-plus"></span> ${__("Create first room")}
						</button>
					</div>
					${this.floor_map.html()}
					${this.fulfillment_hub_host.html()}
					${this.fulfillment_board_host.html()}
				</div>
			</div>
			<div class="sidebar-footer">
				<div class="non-selectable">
					<span class="restaurant-manage-status">${__("Ready")}</span>
					${this.pos_profile_description.html()}
				</div>
			</div>
			<div id="customize-alert-message"></div>
		`);

		this.wrapper.find(".restaurant-empty-rooms-create").on("click", () => {
			this.add_room();
		});
		this.make_fulfillment_navigation();
		this.make_fulfillment_hub();
		this.fulfillment_board = new FulfillmentBoard({
			container: this.wrapper.find(".fulfillment-board-host"),
			on_back: () => this.show_fulfillment_hub(),
			on_counts_change: counts => this.update_fulfillment_counts(counts)
		});
		this.pull_alert("left");
	}

	make_fulfillment_navigation() {
		this.fulfillment_room_count = $("<span>").addClass("badge bg-none").text("0");
		this.fulfillment_room_button = $("<button>")
			.attr({ type: "button", "aria-label": "Pedidos externos" })
			.addClass("btn-default button room fulfillment-room-selector")
			.append(
				this.fulfillment_icon("external-orders", "fulfillment-navigation-icon"),
				document.createTextNode(" Pedidos externos"),
				this.fulfillment_room_count
			)
			.on("click", () => this.show_fulfillment_hub())
			.hide();
	}

	fulfillment_icon(name, class_name) {
		return $("<span>")
			.addClass(`fulfillment-svg-icon ${class_name || ""}`)
			.attr("aria-hidden", "true")
			.append($("<img>", {
				src: `/assets/restaurant_management/restaurant/icons/${name}.svg?v=20260722-2`,
				alt: "",
				draggable: false
			}));
	}

	make_fulfillment_hub() {
		const make_card = (type, icon, title, description) => {
			const count = $("<strong>").addClass("fulfillment-hub-count").text("0");
			const card = $("<button>")
				.attr({ type: "button", "data-fulfillment-type": type })
				.addClass(`fulfillment-hub-card fulfillment-hub-card-${type.toLowerCase()}`)
				.append(
					this.fulfillment_icon(icon, "fulfillment-hub-card-icon"),
					$("<span>").addClass("fulfillment-hub-card-content").append(
						$("<strong>").addClass("fulfillment-hub-card-title").text(title),
						$("<span>").addClass("fulfillment-hub-card-description").text(description),
						$("<span>").addClass("fulfillment-hub-card-total").append(
							count,
							document.createTextNode(" pedidos activos")
						)
					),
					$("<span>").addClass("fa fa-chevron-right fulfillment-hub-card-arrow")
				)
				.on("click", () => this.show_fulfillment(type));
			return { card, count };
		};

		const delivery = make_card(
			"Delivery",
			"delivery-motorcycle",
			"Entrega a domicilio",
			"Pedidos que serán enviados a la dirección del cliente"
		);
		const pickup = make_card(
			"Pickup",
			"pickup-handbag",
			"Recojo en local",
			"Pedidos que el cliente recogerá en el restaurante"
		);
		this.delivery_hub_card = delivery.card;
		this.delivery_hub_count = delivery.count;
		this.pickup_hub_card = pickup.card;
		this.pickup_hub_count = pickup.count;
		this.fulfillment_hub = $("<section>")
			.addClass("fulfillment-hub")
			.append(
				$("<header>").addClass("fulfillment-hub-header").append(
					this.fulfillment_icon("external-orders", "fulfillment-hub-header-icon"),
					$("<div>").append(
						$("<h3>").text("Pedidos externos"),
						$("<p>").text("Selecciona el tipo de atención que deseas gestionar")
					)
				),
				$("<div>").addClass("fulfillment-hub-cards").append(
					this.delivery_hub_card,
					this.pickup_hub_card
				)
			);
		this.wrapper.find(".fulfillment-hub-host").append(this.fulfillment_hub);
	}

	configure_fulfillment_navigation() {
		const restrictions = this.restrictions || {};
		const delivery_enabled = Boolean(Number(restrictions.enable_delivery));
		const pickup_enabled = Boolean(Number(restrictions.enable_pickup));
		const enabled_types = [];
		if (delivery_enabled) enabled_types.push("Delivery");
		if (pickup_enabled) enabled_types.push("Pickup");

		this.delivery_hub_card.toggle(delivery_enabled);
		this.pickup_hub_card.toggle(pickup_enabled);
		this.fulfillment_room_button.toggle(enabled_types.length > 0);
		if (this.fulfillment_board && enabled_types.length) {
			this.fulfillment_board.refresh_counts(enabled_types);
		}
		if (!enabled_types.length && this.fulfillment_room_button.hasClass("active")) {
			this.show_salon();
		}
	}

	update_fulfillment_counts(counts) {
		const delivery = Number(counts.Delivery || 0);
		const pickup = Number(counts.Pickup || 0);
		const total = delivery + pickup;
		this.delivery_hub_count.text(delivery);
		this.pickup_hub_count.text(pickup);
		this.fulfillment_room_count
			.text(total)
			.toggleClass("bg-yellow", total > 0)
			.toggleClass("bg-none", total === 0);
	}

	show_salon() {
		if (!this.floor_map || !this.fulfillment_board) return;
		this.fulfillment_board.hide();
		this.wrapper.find(".fulfillment-board-host, .fulfillment-hub-host").addClass("hide");
		this.floor_map.show();
		this.wrapper.find(".restaurant-manage").removeClass("fulfillment-mode");
		this.fulfillment_room_button.removeClass("active");
	}

	show_fulfillment_hub() {
		if (this.editing) this.set_edit_status();
		if (this.transfer_order) this.cancel_order_transfer(false);
		this.wrapper.find(".floor-selector .button.room").removeClass("active");
		this.fulfillment_room_button.addClass("active");
		this.floor_map.hide();
		this.fulfillment_board.hide();
		this.wrapper.find(".fulfillment-board-host").addClass("hide");
		this.wrapper.find(".fulfillment-hub-host").removeClass("hide");
		this.wrapper.find(".restaurant-manage").addClass("fulfillment-mode");
		this.fulfillment_board.refresh_counts();
	}

	show_fulfillment(fulfillment_type) {
		if (this.editing) this.set_edit_status();
		if (this.transfer_order) this.cancel_order_transfer(false);
		this.wrapper.find(".floor-selector .button.room").removeClass("active");
		this.fulfillment_room_button.addClass("active");
		this.floor_map.hide();
		this.wrapper.find(".fulfillment-hub-host").addClass("hide");
		this.wrapper.find(".fulfillment-board-host").removeClass("hide");
		this.wrapper.find(".restaurant-manage").addClass("fulfillment-mode");
		this.fulfillment_board.show(fulfillment_type);
	}

	close_pos() {
		this.working("Checking opening entries...");
		RM.pos.check_opening_entry(RM.pos_profile.name).then(() => {
			RM.ready();
			const voucher = frappe.model.get_new_doc('POS Closing Entry');
			voucher.pos_profile = this.pos.pos_profile;
			voucher.user = frappe.session.user;
			voucher.company = this.pos.company;
			voucher.pos_opening_entry = this.pos.pos_opening;
			voucher.period_end_date = frappe.datetime.now_datetime();
			voucher.posting_date = frappe.datetime.now_date();

			frappe.set_route('Form', 'POS Closing Entry', voucher.name);
		});
		
	}

	make_rooms() {
		const currents_rooms = Object.values(this.rooms || {}).map(room => room.name);
		this.working("Loading Rooms");
		this.clear_rooms(currents_rooms);

		return new Promise(res => {
			frappe.call({
				method: `${this.url_manage}get_rooms`
			}).then(r => {
				this.rooms = r.message;
				this.render_rooms();
				this.ready();
				
				$("body").show();
				res();
			});
		});
	}

	clear_rooms(currents_rooms = []) {	
		Object.values(this.rooms || {}).forEach(room => {
			if (!currents_rooms.includes(room.name) || !this.has_access_to_room(room.name)) {
				this.object(room.name) ? this.object(room.name).remove() : null;
			}
		});
	}

	set_current_room(room) {
		this.current_room = room;
		this.show_salon();
		this.test_components();
	}

	render_rooms(current = false) {
		let room_from_url = null;

		this.rooms.forEach((room, index, rooms) => {
			const has_access_to_room = this.has_access_to_room(room.name);

			if (this.object(room.name) == null) {
				if (has_access_to_room) {
					this.object(room.name, new RestaurantRoom(room))
				}
			} else {
				if (!has_access_to_room) {
					this.object(room.name).remove();
				} else {
					this.object(room.name).data = room;
				}
			}

			if (current === false) {
				if (this.current_room == null) {
					if (this.object(this.room_from_url) == null) {
						room_from_url = rooms[0].name;
					} else {
						room_from_url = this.room_from_url;
					}
				} else {
					current = true;
					room_from_url = this.current_room.data.name;
				}
			} else {
				room_from_url = current;
			}
		});

		if (this.fulfillment_room_button) {
			this.rooms_container.append(this.fulfillment_room_button);
		}

		this.update_empty_rooms_state();

		setTimeout(() => {
			this.current_room = this.object(room_from_url);

			if (this.current_room != null) {
				if (this.has_access_to_room(this.current_room.data.name)) {
					this.current_room.select();
				} else {
					this.delete_current_room();
				}
			}
		}, 0);
	}

	has_access_to_room(room) {
		return this.rooms_access.includes(room) || frappe.session.user === "Administrator" || this.permissions.restaurant_object.create || this.permissions.restaurant_object.write
	}

	update_empty_rooms_state() {
		const is_empty = !Array.isArray(this.rooms) || this.rooms.length === 0;
		const can_configure = Boolean(this.permissions?.restaurant_object?.write);
		const configured_rooms_count = Number(this.permissions?.configured_rooms_count || 0);
		const has_unassigned_rooms = is_empty && !can_configure && configured_rooms_count > 0;
		const $restaurant = this.wrapper.find(".restaurant-manage");
		const $empty_state = this.wrapper.find(".restaurant-empty-rooms");

		$restaurant.toggleClass("rooms-empty", is_empty);
		$empty_state.toggleClass("hide", !is_empty);
		$empty_state.find(".restaurant-empty-rooms-create").toggle(can_configure);
		$empty_state.find(".restaurant-empty-rooms-title").text(
			has_unassigned_rooms ? __("No rooms assigned") : __("No rooms configured")
		);
		$empty_state.find(".restaurant-empty-rooms-help").text(
			has_unassigned_rooms
				? __("Ask a restaurant administrator to assign rooms for {0} in the POS Profile.", [this.company])
				: can_configure
				? __("Create the first room to start adding tables and production centers for {0}.", [this.company])
				: __("Ask a restaurant administrator to configure rooms for {0}.", [this.company])
		);
	}

	get settings_data() {
		return new Promise(res => {
			frappe.xcall(`${this.url_manage}get_settings_data`, {}).then(r => {
				this.set_settings_data(r);
				res();
			});
		});
	}

	set_settings_data(r) {
		this.loaded = true;
		this.#permissions = r.permissions;
		this.#exceptions = r.exceptions;
		this.#restrictions = r.restrictions;
		this.#lang = r.lang;
		this.restaurant_permissions = r.pos.restaurant_permissions;
		this.order_item_editor_form = r.order_item_editor_form;
		this.configure_fulfillment_navigation();

		if (r.pos.has_pos) {
			this.#pos_profile = r.pos.pos;
			if (this.pos_profile != null) {
				this.pos_profile_description.val(this.pos_profile.name);
			}
		}
		this.ready();
	}

	get pos_profile() { return this.#pos_profile }
	get permissions() { return this.#permissions }
	get exceptions() { return this.#exceptions }
	get restrictions() { return this.#restrictions }
	get company() { return this.pos_profile.company }
	get components() { return this.#components }
	get lang() { return this.#lang }

	in_rooms(f) {
		this.rooms.forEach((room, index, rooms) => {
			if (RM.object(room.name) != null) {
				f(RM.object(room.name), index, rooms)
			}
		});
	}

	object(name, object = null) {
		const obj = this.objects[name];
		if (typeof obj == "undefined" && object != null) {
			this.objects[name] = object;
		}
		return typeof this.objects[name] != "undefined" ? this.objects[name] : null;
	}

	begin_order_transfer(order) {
		this.transfer_order = order;
		const source_table = order.order_manage.table.data.description;
		const order_name = order.data.short_name || order.data.name;
		const message = __(
			"Transferring order {0} from {1}. Select the destination table.",
			[order_name, source_table]
		);

		this.transfer_notice_text.val(frappe.utils.escape_html(message));
		this.transfer_notice.remove_class("hide");
		this.wrapper.find(".restaurant-manage").addClass("transfer-mode");
		this.working("Transferring Order");
	}

	hide_transfer_notice() {
		if (this.transfer_notice) this.transfer_notice.add_class("hide");
		this.wrapper.find(".restaurant-manage").removeClass("transfer-mode");
	}

	cancel_order_transfer(reopen_source = true) {
		const order = this.transfer_order;
		this.transfer_order = null;
		this.hide_transfer_notice();
		this.ready({ message: __("Transfer cancelled"), indicator: "orange" });

		if (reopen_source && order && order.order_manage) {
			setTimeout(() => order.order_manage.show());
		}
	}

	reconcile_order_transfer(payload) {
		const event = payload && payload.transfer_event ? payload.transfer_event : payload;
		const order = event && event.data && event.data.order;
		if (!order || !order.data) return;
		this.request_client = event.client;

		const destination_table = this.object(order.data.table);
		const source_table = this.object(order.data.last_table);
		if (payload && payload.source_table && source_table) {
			source_table.reset_data(payload.source_table);
		}
		if (payload && payload.destination_table && destination_table) {
			destination_table.reset_data(payload.destination_table);
		}

		if (source_table && source_table.order_manage) {
			source_table.order_manage.remove_transferred_order(order.data.name);
		}

		this.transfer_order = null;
		this.hide_transfer_notice();
		if (!destination_table) return;

		if (destination_table.order_manage == null) {
			if (this.client === event.client && !destination_table.transfer_manage_pending) {
				destination_table.transfer_manage_pending = true;
				setTimeout(() => {
					destination_table.order_manage = new OrderManage({
						identifier: this.OMName(destination_table.data.name),
						table: destination_table,
						current_order_identifier: order.data.name
					});
					this.object(destination_table.order_manage.identifier, destination_table.order_manage);
					destination_table.transfer_manage_pending = false;
				});
			}
			return;
		}

		setTimeout(() => {
			destination_table.order_manage.receive_transferred_order(event);
			if (
				destination_table.room.data.name === this.current_room.data.name &&
				this.client === event.client
			) {
				destination_table.order_manage.show();
			}
		});
	}

	start_table_reconciliation() {
		if (this.table_reconciliation_interval) {
			clearInterval(this.table_reconciliation_interval);
		}

		this.table_reconciliation_interval = setInterval(() => {
			if (RM !== this) {
				clearInterval(this.table_reconciliation_interval);
				return;
			}
			if (!document.hidden && this.current_room && !this.editing && !this.busy) {
				this.current_room.get_tables(true);
			}
		}, 5000);
	}

	init_synchronize() {
		frappe.realtime.on("debug_data", (data) => {
			console.log(data);
		});

		const check_items_in_process_manage = (items, item_removed = null) => {
			this.in_rooms(room => {
				room.in_tables(table => {
					if (table.process_manage != null) {
						table.process_manage.check_items(items);
						if (item_removed) {
							table.process_manage.remove_item(item_removed);
						}
					}
				});
			});
		}

		frappe.realtime.on("synchronize_order_data", (r) => {
			const data = r.data;
			const order = data.order;

			this.request_client = r.client;
			check_items_in_process_manage(data.items, r.item_removed);

			const table = RM.object(order.data.table);
			if (this.current_room == null || table == null) return;

			if (r.action === TRANSFER) {
				this.reconcile_order_transfer(r);
			} else {
				if (table.order_manage != null) {
					const local_order = table.order_manage.get_order(order.data.name);
					if (local_order && local_order.has_pending_item_mutations()) {
						// The direct response of the final queued mutation will carry
						// the authoritative quantity. Applying an earlier realtime
						// event here could restore a stale value between rapid clicks.
						return;
					}
					setTimeout(() => {
						table.order_manage.check_data(r);
					});
				}
			}
		});

		frappe.realtime.on("update_settings", (data) => {
			if (data && data.company && data.company !== this.bootstrap.company) return;
			this.settings_data.then(() => {
				this.make_rooms();
				this.check_permissions_status();
			});
		});

		frappe.realtime.on("check_rooms", (r) => {
			this.sync_rooms(r);
			if (r && r.company && r.company !== this.bootstrap.company) return;
		});

		frappe.realtime.on("pos_profile_update", (r) => {
			if (r && r.has_pos) {
				this.#pos_profile = r.pos;
			} else {
				this.#pos_profile = null;
				this.raise_exception_for_pos_profile();
			}
		});

		this.start_table_reconciliation();
	}

	get rooms_access() {
		return Object.values((this.permissions || {}).rooms_access || []);
	}

	check_permissions_status() {
		this.in_rooms((Room) => {
			Room.in_tables((Table) => {
				if (Table.order_manage != null) {
					Table.order_manage.check_permissions_status();
				}
				Table.set_orders_count();
			}, "Table");
		});

		if (!this.permissions.restaurant_object.write) {
			this.general_edit_button.disable().hide();
		}
	}

	add_object(t) {
		if (t === "Room") {
			this.add_room();
		} else if (this.current_room != null) {
			this.current_room.add_object(t);
		}
	}

	add_room() {
		this.working("Add Room");
		frappe.call({
			method: this.url_manage + "add_room",
			args: { client: RM.client },
			callback: (r) => {
				if (r.message) this.sync_rooms(r.message);
			},
			always: () => {
				this.ready();
			},
		});
	}

	sync_rooms(data) {
		this.rooms = data.rooms || [];

		this.settings_data.then(() => {
			this.rooms = this.rooms.filter(room => this.has_access_to_room(room.name));
			this.render_rooms(data.client === RM.client ? data.current_room : false);
		});
	}

	set_edit_status() {
		if (!this.permissions.restaurant_object.write) return;
		if (this.editing) {
			this.editing = false;
			$(".restaurant-manage").removeClass("editing");
			this.unselect_all_tables();
		} else {
			this.editing = true;
			$(".restaurant-manage").addClass("editing");
			Object.keys(this.components).forEach(k => {
				this.#components[k].hide();
			});
			this.test_components();
		}
	}

	test_components() {
		Object.keys(this.components).forEach(k => {
			if (this.current_room == null) {
				this.#components[k].hide();
			} else {
				this.#components[k].show();
			}
		});
	}

	get room_from_url() {
		return frappe.urllib.get_arg("restaurant_room");
	}

	unselect_all_tables() {
		this.in_rooms((room) => {
			room.unselect_all_tables();
		});
	}

	pull_alert(position = "right", max_width = "calc(100% - 410px)") {
		$("#customize-alert-message").empty().append(`
			<style>
				#alert-container{
					${position}: 10px !important;
					max-width: ${max_width} !important;
					-moz-user-select: none;
					-webkit-user-select: none;
					-ms-user-select: none;
					user-select: none;
					z-index: 999999999999999999999;
				}
			</style>`
		)
	}

	delete_current_room() {
		this.current_room = null;
		// frappe.set_route(`/restaurant-manage?restaurant_room=?`);
		this.test_components();
	}

	working(text, busy = true) {
		this.busy = busy;
		this.wrapper.find(".restaurant-manage-status").empty().append(__(text));
	}

	ready(message = false, sound = false) {
		this.busy = false;
		if (RM.transfer_order != null) {
			this.working("Transferring Order");
		} else {
			this.wrapper.find(".restaurant-manage-status").empty().append(__("Ready"))
		}

		if (message !== false) {
			frappe.show_alert(message);
		}

		if (sound !== false) {
			setTimeout(`window['RM'].sound_${sound}()`, 0)
		}
	}

	busy_message() {
		if (this.busy) {
			frappe.show_alert({
				indicator: 'red',
				message: __("Please wait for an operation to complete")
			});
			return true;
		}
		return false;
	}

	notification(indicator = "red", message = "") {
		frappe.show_alert({
			indicator: indicator,
			message: __(message)
		});
	}

	format_currency(value) {
		const val = isNaN(parseFloat(value)) ? 0 : parseFloat(value);
		return format_currency(parseFloat(val), this.pos_profile.currency);
	}

	sound_delete(message = false) {
		if (this.sounds) $("#sound-delete").trigger('play');
		if (message !== false) {
			frappe.show_alert(message);
		}
	}
	sound_submit(message = false) {
		if (this.sounds) $("#sound-submit").trigger('play');

		if (message !== false) {
			frappe.show_alert(message);
		}
	}
	sound_success(message = false) {
		if (this.sounds) $("#sound-submit").trigger('play');

		if (message !== false) {
			frappe.show_alert(message);
		}
	}

	uuid(prefix = 'obj') {
		const id = 'xxxx-xx-4xx-yxx-xxxxx'.replace(/[xy]/g, function (c) {
			const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
			return v.toString(16);
		});

		return prefix + "_" + id;
	}

	check_permissions(model = null, record = null, action) {
		if (frappe.session.user === "Administrator") return true;

		let r = false;

		if (model != null) {
			let model_in_permissions = this.permissions[model];
			if (typeof model_in_permissions != "undefined" && typeof model_in_permissions[action] !== "undefined") {
				r = this.permissions[model][action];
			}

			const exception = () => {
				r = false;
				this.exceptions.map(e => {
					r = e[model + "_" + action] === 1;
				});
			}

			if (record == null) {
				if (!r) {
					exception();
				}
			} else {
				if (record.data.owner !== frappe.session.user) {
					if (model === "order" && this.restrictions.restricted_to_owner_order) {
						exception();
					}
					if (model === "table" && this.restrictions.restricted_to_owner_table) {
						exception();
					}
				}
			}

			if (model === 'pos' && r) {
				r = this.pos_profile["allow_" + action] === 1;
			}
		}

		return r;
	}

	get can_pay() {
		return this.check_permissions("invoice", null, "create");
	}

	can_open_order_manage(table) {
		if (frappe.session.user === "Administrator" || this.can_pay) return true;

		if (table.data.current_user !== frappe.session.user && table.data.orders_count > 0) {
			if (this.restrictions.restricted_to_owner_table) {
				return this.check_permissions("order", null, "manage");
			}
		}

		return true;
	}

	PMName(process_manage) { return "process_manage" + process_manage; }
	OMName(order_manage) { return "order_manage" + order_manage; }
}
