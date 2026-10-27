const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "fulfillment-board-class.js"), "utf8");

class Element {
    constructor(tag) {
        this.tag = tag;
        this.classes = new Set();
        this.children = [];
        this.attributes = {};
        this.handlers = {};
    }
    addClass(names) { names.split(" ").forEach(name => this.classes.add(name)); return this; }
    removeClass(names) { names.split(" ").forEach(name => this.classes.delete(name)); return this; }
    hasClass(name) { return this.classes.has(name); }
    toggleClass(name, enabled) { return enabled ? this.addClass(name) : this.removeClass(name); }
    attr(values) { Object.assign(this.attributes, values); return this; }
    append(...children) { this.children.push(...children); return this; }
    prepend(...children) { this.children.unshift(...children); return this; }
    empty() { this.children = []; return this; }
    text(value) { if (value === undefined) return this.content; this.content = value; return this; }
    val(value) { if (value === undefined) return this.value; this.value = value; return this; }
    on(event, handler) { this.handlers[event] = handler; return this; }
}

function fixture() {
    const requests = [];
    const timers = new Map();
    const intervals = [];
    const events = {};
    const documentEvents = {};
    let timerID = 0;
    const context = vm.createContext({
        $: tag => tag instanceof Element ? tag : new Element(tag),
        __: message => message,
        document: {
            hidden: false,
            createTextNode: text => text,
            addEventListener: (event, handler) => { documentEvents[event] = handler; },
        },
        setTimeout: callback => { timers.set(++timerID, callback); return timerID; },
        clearTimeout: id => timers.delete(id),
        setInterval: callback => { intervals.push(callback); return intervals.length; },
        frappe: {
            datetime: {
                system_datetime: () => "2026-10-26 00:30:00",
                get_today: () => "2026-10-25", // User timezone must not select the site's previous day.
            },
            realtime: { on: (event, handler) => { events[event] = handler; } },
            call(options) {
                requests.push(options);
                if (options.method.endsWith("get_fulfillment_counts")) {
                    return Promise.resolve({ message: { Delivery: 2, Pickup: 1 } });
                }
                return Promise.resolve({});
            },
        },
    });
    vm.runInContext(`${source}\nglobalThis.TestBoard = FulfillmentBoard;`, context);
    const countUpdates = [];
    const board = new context.TestBoard({
        container: new Element("container"),
        on_counts_change: counts => countUpdates.push({ ...counts }),
    });
    const runTimers = () => {
        const pending = [...timers.values()];
        timers.clear();
        pending.forEach(callback => callback());
    };
    const boardRequests = () => requests.filter(request => request.method.endsWith("get_fulfillment_board"));
    return { board, context, requests, boardRequests, countUpdates, runTimers, intervals, events, documentEvents };
}

test("pickup offers a compact date filter initially using the site's day", () => {
    const { board, boardRequests } = fixture();
    board.show("Pickup");
    assert.equal(board.completed_date, "2026-10-26");
    assert.equal(board.completed_date_input.attributes.type, "date");
    assert.match(board.completed_date_input.attributes["aria-label"], /recogidos/);
    assert.equal(board.completed_date_filter.hasClass("hide"), false);
    assert.deepEqual({ ...boardRequests()[0].args }, { fulfillment_type: "Pickup", completed_date: "2026-10-26" });
});

test("date change requests that day and an empty value resets to site today", () => {
    const { board, boardRequests } = fixture();
    board.show("Pickup");
    board.completed_date_input.val("2026-10-24").handlers.change();
    assert.equal(boardRequests().at(-1).args.completed_date, "2026-10-24");
    board.completed_date_input.val("").handlers.change();
    assert.equal(boardRequests().at(-1).args.completed_date, "2026-10-26");
});

test("Delivery requests keep their existing arguments and hide the pickup filter", () => {
    const { board, boardRequests } = fixture();
    board.show("Delivery");
    assert.equal(board.completed_date_filter.hasClass("hide"), true);
    assert.deepEqual({ ...boardRequests()[0].args }, { fulfillment_type: "Delivery" });
});

test("paid collected cards remain visible without inflating pending badges", async () => {
    const state = fixture();
    state.board.show("Pickup");
    state.board.card = row => new Element(row.name);
    state.boardRequests()[0].always({ message: [
        { name: "PENDING", status: "Ready", payment_status: "Unpaid" },
        { name: "CLOSED-1", status: "Picked Up", payment_status: "Paid" },
        { name: "CLOSED-2", status: "Picked Up", payment_status: "Paid" },
    ] });
    const collectedColumn = state.board.columns_wrapper.children.find(
        column => column.hasClass("fulfillment-status-picked-up")
    );
    assert.equal(collectedColumn.children[0].children[1].text(), 2);
    assert.equal(collectedColumn.children[1].children.length, 2);
    assert.equal(state.board.counts.Pickup, 0); // No rows.length assignment.
    state.runTimers();
    await Promise.resolve();
    assert.equal(state.board.counts.Pickup, 1);
    assert.equal(state.board.counts.Delivery, 2);
    assert.deepEqual(state.countUpdates.at(-1), { Delivery: 2, Pickup: 1 });
});

test("a delayed response for the old date cannot replace the selected day", () => {
    const state = fixture();
    const rendered = [];
    state.board.render = rows => rendered.push(rows);
    state.board.show("Pickup");
    state.board.completed_date_input.val("2026-10-25").handlers.change();
    const [oldRequest, newRequest] = state.boardRequests();
    newRequest.always({ message: [{ name: "SELECTED" }] });
    oldRequest.always({ message: [{ name: "STALE" }] });
    assert.deepEqual(rendered, [[{ name: "SELECTED" }]]);
});

test("an old response cannot clear the loading indicator of a newer request", () => {
    const state = fixture();
    state.board.render = () => {};
    state.board.show("Pickup");
    state.board.reload();
    state.boardRequests()[0].always({ message: [] });
    assert.equal(state.board.columns_wrapper.hasClass("loading"), true);
    state.boardRequests()[1].always({ message: [] });
    assert.equal(state.board.columns_wrapper.hasClass("loading"), false);
});

test("hiding the board or switching service ignores obsolete responses", () => {
    const state = fixture();
    const rendered = [];
    state.board.render = rows => rendered.push(rows);
    state.board.show("Pickup");
    state.board.hide();
    state.boardRequests()[0].always({ message: [{ name: "HIDDEN" }] });
    assert.equal(rendered.length, 0);
    state.board.show("Pickup");
    state.board.show("Delivery");
    state.boardRequests()[1].always({ message: [{ name: "PICKUP" }] });
    state.boardRequests()[2].always({ message: [{ name: "DELIVERY" }] });
    assert.deepEqual(rendered, [[{ name: "DELIVERY" }]]);
});

test("realtime, polling and returning from Delivery preserve the selected pickup date", () => {
    const state = fixture();
    state.board.show("Pickup");
    state.board.completed_date_input.val("2026-10-24").handlers.change();
    state.events.restaurant_fulfillment_update({ fulfillment_type: "Pickup" });
    state.runTimers();
    assert.equal(state.boardRequests().at(-1).args.completed_date, "2026-10-24");
    state.intervals[0]();
    assert.equal(state.boardRequests().at(-1).args.completed_date, "2026-10-24");
    state.board.show("Delivery");
    state.board.show("Pickup");
    assert.equal(state.boardRequests().at(-1).args.completed_date, "2026-10-24");
});

test("rejected board responses never set pending counts from stale visible rows", () => {
    const state = fixture();
    state.board.show("Pickup");
    state.boardRequests()[0].always({ exc: "Error" });
    assert.equal(state.board.columns_wrapper.hasClass("loading"), false);
    assert.equal(state.countUpdates.length, 0);
});
