# Design

The facade resolves the active company and POS Profile on every call. Mutations are idempotent, lock the authoritative order and compare its version before work. Customer records require read access, discount depends on the POS Profile flag, division requires order creation, and transfer validates the destination table scope before invoking the existing document method.
