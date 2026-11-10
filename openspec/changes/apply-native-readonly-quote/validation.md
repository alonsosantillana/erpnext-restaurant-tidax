# Native Application Evidence

2026-11-10. Owner-authorized code-only application on the existing v16 site.
Original037c8a1dcb7b6ff968345658eab2da2834a5d6b0; applied reviewed target
8138a203778bda8a2851c1ee4c19feb35f16b4e9. TIX's final paired target is the reviewed
dispatch-correction descendant c0daa3cbdba86c0517206b44d2d00ace0141fe3a.

Initial application exposed a TIX-only RPC dispatch validation defect. The original
guarded pair was restored while that defect was reproduced, narrowly fixed,
independently reviewed and published. The native target itself did not change.
The pair was then reapplied after clean-source checks with command-scoped Git
hooks disabled. Native hooks and authentication finalizers remain unchanged.

Installed-origin paired quote/search/review/native tests:144 passed. Installed-
origin read/auth qualification:235 passed, zero skips/errors/failures/protected
I/O attempts. Frappe16.55.2, ERPNext16.54.0, benchPython3.14.3. No site initialized
by offline tests. Existing actual live reads/denials/health also passed after the
corrected pair. See paired TIX application evidence for exact bounded results.

External runtime source was separately updated to ff350ff; a new independent
session registered51 read tools and searched successfully. The owner's native
chat session still needs reconnection. Live quote readiness is NOT accepted:
the site's quote configuration currently denies it with403. No option was enabled,
and real customer/owned delivery-address references remain pending.

No migration, schema, stock/order/invoice/payment record, price/tax setting,
permission, provider, dependency, cache reset or explicit service command changed.
Development autoreload may react to source checkouts. Main refs remain untouched.
Recovery is the original guarded source after concurrent-change checks; no data
or schema reversal is needed. Evidence branch publication is verified at delivery.
