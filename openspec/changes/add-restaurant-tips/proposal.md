## Why

Restaurant Management previously represented tips as a special POS payment method. In
ERPNext v15 an additional payment row increases paid_amount and can be treated as
change, mixing worker funds with the taxable restaurant sale.

## What Changes

- Add company-specific tip enablement and a mandatory tip payable account.
- Capture the tip amount and collection method independently in the payment dialog.
- Create a Restaurant Tip record linked to the order and POS Invoice.
- Post collection to the selected cash/bank account against the tip payable liability.
- Keep the tip outside POS Invoice totals, taxes, discounts, and the Nubefact payload.
- Cancel the tip accounting when its POS Invoice is cancelled.
- Replace the legacy payment-row tip report with company-isolated Restaurant Tip
  reporting.

## Impact

- Affected app: restaurant_management.
- Affected flow: payment, POS accounting, cancellation, closing reports.
- New DocType: Restaurant Tip.
- Existing POS Invoice fiscal totals remain unchanged.
