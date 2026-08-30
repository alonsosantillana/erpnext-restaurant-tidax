const test = require("node:test");
const assert = require("node:assert/strict");

global.DeskForm = class {};

const {
    restaurant_payment_amount,
    restaurant_payment_input_value,
    restaurant_normalize_payment_allocations,
    restaurant_payment_distribution
} = require("./pay-form-class.js");

test("uses the internal NumPad value while pad editing is active", () => {
    assert.equal(restaurant_payment_input_value(true, 9, 18), 9);
    assert.equal(restaurant_payment_input_value(false, 9, "12.50"), "12.50");
});

test("normalizes valid positive payment amounts", () => {
    assert.equal(restaurant_payment_amount("12,345"), 12.35);
    assert.equal(restaurant_payment_amount("invalid"), 0);
    assert.equal(restaurant_payment_amount(-3), 0);

    assert.deepEqual(
        restaurant_normalize_payment_allocations({
            Efectivo: "10.126",
            "BCP SOL": 8.5,
            Vacio: 0,
            Invalido: "x"
        }),
        { Efectivo: 10.13, "BCP SOL": 8.5 }
    );
});

test("calculates a simple payment without pending amount or change", () => {
    assert.deepEqual(
        restaurant_payment_distribution(18, { Efectivo: 18 }),
        {
            payments: { Efectivo: 18 },
            paid: 18,
            pending: 0,
            change: 0
        }
    );
});

test("calculates mixed payments using one allocation per payment method", () => {
    const allocations = { Efectivo: 10 };
    allocations.Efectivo = 8;
    allocations["BCP SOL"] = 10;

    assert.deepEqual(
        restaurant_payment_distribution(18, allocations),
        {
            payments: { Efectivo: 8, "BCP SOL": 10 },
            paid: 18,
            pending: 0,
            change: 0
        }
    );
});

test("calculates pending amount and change independently", () => {
    assert.equal(
        restaurant_payment_distribution(18, { Efectivo: 10 }).pending,
        8
    );
    assert.equal(
        restaurant_payment_distribution(18, { Efectivo: 20 }).change,
        2
    );
});

test("removing or zeroing an allocation excludes it from the backend map", () => {
    assert.deepEqual(
        restaurant_payment_distribution(18, {
            Efectivo: 18,
            "BCP SOL": 0
        }).payments,
        { Efectivo: 18 }
    );
});
