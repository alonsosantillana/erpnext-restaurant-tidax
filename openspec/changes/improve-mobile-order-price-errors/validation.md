# Validation

## Completed before implementation

- The POS Profile `Resto2` resolves selling price list `Resto SOL` in PEN.
- Five QA catalog items have a positive active selling price.
- A transactional test added `BEB-001` temporarily and reported `ADD_ITEM_OK`; the savepoint was rolled back.
- Graphify linked `mutate_item` to `_new_item_entry` and the common error helper; direct code review confirmed the runtime path.
- Direct code review confirmed `TableOrder.send` is a property.

## Automated validation

```text
python -m py_compile restaurant_management/mobile_api/v1.py restaurant_management/mobile_api/test_v1.py
```

- Result: successful.

```text
python -m unittest restaurant_management.mobile_api.test_v1 -v
```

- Result: 18 tests passed in 0.112 seconds.
- Tests use mocks for mutation paths and did not write business data.

```text
openspec validate improve-mobile-order-price-errors --strict
```

- Result: `Change 'improve-mobile-order-price-errors' is valid`.

```text
GRAPHIFY_QUERY_LOG_DISABLE=1 graphify extract . --code-only
```

- Result: 2 code files re-extracted; 2,859 nodes, 4,326 edges and 328 communities.
- No document, image or remote/LLM extraction was used; generated artifacts remain ignored by Git.

## Git review

- Branch: `fix/mobile-order-price-validation`.
- `git diff --check`: successful.
- Tracked code changes: 2 files, 89 inserted test/validation lines.
- OpenSpec change: 5 new Markdown files.
- No credential, migration, fixture, hook, DocType or site configuration was added.

## UAT

- BFF/mobile API validated successfully by the user before integration to the main branch.
