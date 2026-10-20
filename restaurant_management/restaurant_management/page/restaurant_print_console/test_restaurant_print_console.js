const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "restaurant_print_console.js"), "utf8");
const methods = ["connect", "reconnect", "close", "getState", "isConnected", "submit"];

function fixture({ initial = "modern", load, stored_id } = {}) {
    const requests = [];
    const printers = [];
    const storage = new Map();
    if (stored_id) storage.set("restaurant_print_station_client", stored_id);
    const chain = {
        find() { return this; },
        remove() { return this; },
        appendTo() { return this; },
        html() { return this; },
    };
    const modern_client = () => {
        class Printer {
            constructor(options) {
                this.options = options;
                printers.push(this);
            }
        }
        for (const method of methods) Printer.prototype[method] = () => {};
        return { make_id: () => "generated-client-id", WebSocketPrinter: Printer };
    };
    const frappe = {
        pages: { "restaurant-print-console": {} },
        silent_print: initial === "modern" ? modern_client() : initial,
        async require(asset) {
            requests.push(asset);
            if (load) await load(frappe, modern_client);
        },
    };
    const wrapper = { page: { main: chain, set_primary_action() {}, set_secondary_action() {} } };
    const context = vm.createContext({
        frappe,
        $: () => chain,
        __: text => text,
        sessionStorage: {
            getItem: key => storage.get(key) || null,
            setItem: (key, value) => storage.set(key, value),
        },
    });
    vm.runInContext(source, context);
    return { context, frappe, modern_client, wrapper, requests, printers, storage };
}

test("upgrades a legacy constructor before creating the station", async () => {
    const state = fixture({
        initial: { WebSocketPrinter: function LegacyPrinter() {} },
        load(frappe, modern) { frappe.silent_print = modern(); },
    });

    const controller = await state.context.get_restaurant_print_station_controller(state.wrapper);

    assert.deepEqual(state.requests, ["/assets/silent_print/js/silent_print_v15.js"]);
    assert.equal(controller.client_id, "generated-client-id");
    assert.equal(state.printers.length, 1);
    assert.equal(state.storage.get("restaurant_print_station_client"), controller.client_id);
});

test("loads the modern client when the Silent Print namespace is absent", async () => {
    const state = fixture({
        initial: undefined,
        load(frappe, modern) { frappe.silent_print = modern(); },
    });
    delete state.frappe.silent_print;

    await state.context.get_restaurant_print_station_controller(state.wrapper);

    assert.equal(state.requests.length, 1);
    assert.equal(state.printers.length, 1);
});

test("reuses a complete client and preserves its session identifier", async () => {
    const state = fixture({ stored_id: "existing-client-id" });

    const first = await state.context.get_restaurant_print_station_controller(state.wrapper);
    const second = await state.context.get_restaurant_print_station_controller(state.wrapper);

    assert.equal(first, second);
    assert.equal(first.client_id, "existing-client-id");
    assert.equal(state.requests.length, 0);
    assert.equal(state.printers.length, 1);
});

test("reloads a modern constructor when make_id is missing or not callable", async () => {
    for (const make_id of [undefined, "not a function"]) {
        const state = fixture({
            load(frappe, modern) { frappe.silent_print = modern(); },
        });
        state.frappe.silent_print.make_id = make_id;

        await state.context.get_restaurant_print_station_controller(state.wrapper);

        assert.equal(state.requests.length, 1);
        assert.equal(state.printers.length, 1);
    }
});

test("reloads when any required lifecycle method is missing", async () => {
    for (const method of methods) {
        const state = fixture({
            load(frappe, modern) { frappe.silent_print = modern(); },
        });
        delete state.frappe.silent_print.WebSocketPrinter.prototype[method];

        await state.context.get_restaurant_print_station_controller(state.wrapper);

        assert.equal(state.requests.length, 1, method);
        assert.equal(state.printers.length, 1, method);
    }
});

test("rejects a non-callable printer constructor before construction", async () => {
    const state = fixture({ initial: { make_id() {}, WebSocketPrinter: {} } });

    await assert.rejects(
        state.context.get_restaurant_print_station_controller(state.wrapper),
        /Actualice.*silent_print/
    );

    assert.equal(state.printers.length, 0);
    assert.equal(state.wrapper.page.station_controller, undefined);
});

test("reports an incompatible asset without creating a controller", async () => {
    const state = fixture({ initial: { WebSocketPrinter: function LegacyPrinter() {} } });

    await assert.rejects(
        state.context.get_restaurant_print_station_controller(state.wrapper),
        /Actualice.*silent_print/
    );

    assert.equal(state.requests.length, 1);
    assert.equal(state.wrapper.page.station_controller, undefined);
    assert.equal(state.printers.length, 0);
});

test("reports an asset loading failure without constructing a printer", async () => {
    const state = fixture({
        initial: null,
        load() { throw new Error("asset unavailable"); },
    });

    await assert.rejects(
        state.context.get_restaurant_print_station_controller(state.wrapper),
        /Actualice.*silent_print/
    );

    assert.equal(state.wrapper.page.station_controller, undefined);
    assert.equal(state.printers.length, 0);
});
