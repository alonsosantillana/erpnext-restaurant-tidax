from decimal import Decimal, InvalidOperation


class PayloadError(ValueError):
    pass


def decimal_value(value, label, default=None):
    if value in (None, "") and default is not None:
        return Decimal(str(default))
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PayloadError(f"{label} is not a valid amount") from exc


def delivery_mode(payload):
    expedition = str(payload.get("expeditionType") or "").lower()
    if expedition == "pickup":
        return "Pickup", "Customer Pickup"
    if expedition != "delivery":
        raise PayloadError("expeditionType must be delivery or pickup")
    delivery = payload.get("delivery") or {}
    provider = "PedidosYa" if delivery.get("riderPickupTime") else "Restaurant"
    return "Delivery", provider


def address_snapshot(payload):
    address = (payload.get("delivery") or {}).get("address") or {}
    parts = []
    for key in ("street", "number", "floor", "apartment", "city", "district", "zipCode"):
        value = str(address.get(key) or "").strip()
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts)


def contact_phone(payload):
    customer = payload.get("customer") or {}
    return str(customer.get("mobilePhone") or customer.get("phone") or "").strip()


def promised_at(payload):
    delivery = payload.get("delivery") or {}
    pickup = payload.get("pickup") or {}
    return delivery.get("riderPickupTime") or pickup.get("pickupTime") or payload.get("preOrderPickupTime")


def external_total(payload):
    price = payload.get("price") or {}
    for key in ("grandTotal", "total", "totalNet", "paid"):
        if price.get(key) not in (None, ""):
            return decimal_value(price[key], f"price.{key}")
    return None


def delivery_fee(payload):
    price = payload.get("price") or {}
    fees = price.get("deliveryFees")
    if isinstance(fees, list):
        total = sum(
            (decimal_value(row.get("value"), "price.deliveryFees.value", 0) for row in fees),
            Decimal("0"),
        )
        if total < 0:
            raise PayloadError("price.deliveryFees cannot be negative")
        return total
    value = price.get("deliveryFee")
    if value in (None, ""):
        return Decimal("0")
    fee = decimal_value(value, "price.deliveryFee")
    if fee < 0:
        raise PayloadError("price.deliveryFee cannot be negative")
    return fee


def normalize_lines(payload, mappings):
    products = payload.get("products")
    if not isinstance(products, list) or not products:
        raise PayloadError("products must contain at least one item")

    lines = []
    missing = set()
    for product in products:
        product_quantity = decimal_value(product.get("quantity"), "product.quantity", 1)
        toppings = list(_flatten_toppings(product.get("selectedToppings") or [], product_quantity))
        topping_total = sum((row[1] * row[2] for row in toppings), Decimal("0"))
        product_source = dict(product)
        topping_notes = [
            f"{row[0].get('name')} x {row[1]}"
            for row in toppings
            if row[0].get("name")
        ]
        product_source["comment"] = "; ".join(
            part for part in [str(product.get("comment") or "").strip(), ", ".join(topping_notes)] if part
        )
        _append_line(lines, missing, product_source, mappings, "Product", included_topping_total=topping_total)
        for topping, quantity, rate in toppings:
            _append_line(
                lines,
                missing,
                topping,
                mappings,
                "Topping",
                quantity_override=quantity,
                rate_override=rate,
            )
    if missing:
        raise PayloadError("Unmapped remoteCode values: " + ", ".join(sorted(missing)))
    return lines


def _flatten_toppings(toppings, parent_quantity):
    for topping in toppings:
        quantity = decimal_value(topping.get("quantity"), "topping.quantity", 1) * parent_quantity
        rate = decimal_value(topping.get("price"), "topping.price", 0)
        yield topping, quantity, rate
        yield from _flatten_toppings(topping.get("children") or [], quantity)


def _append_line(
    lines,
    missing,
    source,
    mappings,
    kind,
    included_topping_total=Decimal("0"),
    quantity_override=None,
    rate_override=None,
):
    if kind == "Topping" and rate_override == 0:
        return
    remote_code = str(source.get("remoteCode") or "").strip()
    mapping = mappings.get(remote_code)
    if not remote_code or not mapping:
        missing.add(remote_code or "<empty>")
        return
    quantity = quantity_override or decimal_value(source.get("quantity"), f"{remote_code}.quantity", 1)
    if quantity <= 0:
        raise PayloadError(f"{remote_code}.quantity must be greater than zero")

    paid_price = source.get("paidPrice")
    if rate_override is not None:
        rate = rate_override
    elif paid_price not in (None, ""):
        base_total = decimal_value(paid_price, f"{remote_code}.paidPrice") - included_topping_total
        if base_total < 0:
            raise PayloadError(f"{remote_code}.paidPrice is lower than its topping total")
        rate = base_total / quantity
    else:
        rate = decimal_value(
            source.get("unitPrice", source.get("price")),
            f"{remote_code}.unitPrice",
            0,
        )
    if rate < 0:
        raise PayloadError(f"{remote_code}.price cannot be negative")
    lines.append({
        "remote_code": remote_code,
        "item_code": mapping.item_code,
        "kind": kind,
        "qty": quantity,
        "rate": rate,
        "notes": str(source.get("comment") or "").strip(),
    })
