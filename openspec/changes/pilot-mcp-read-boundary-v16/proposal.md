# Bounded V16 Backend Pilot: Restaurant

## Why And Authorization

The owner approved preparing and installing the five reviewed backend files in
the existing v16 site, then checking ordinary HTTP reads. Activation of the
restricted account is explicitly separate. This is a bounded qualification pilot,
not general v16 package acceptance or a maintenance merge.

## Scope And Sources

Preserve installed base 9466ba8190d71e144505e22c06b66d8ab59ea98a and its existing
work, including Restaurant's minimarket coexistence documentation. Transfer only
restaurant_management/hooks.py, restaurant_management/integrations/auth_finalizer.py
from reviewed source 5211f6eae12f86c6c292bc08829a5168fa30745c.
The companion TIX repository has the same pilot change identifier.
Documentation and a reproducible synthetic source harness may accompany it.

## Risk And Exclusions

High risk: native authentication hooks span two apps. No core edit, DocType,
patch, fixture, migration, dependency installation, external MCP package change,
marker role creation/assignment, permission/configuration/cache modification,
service command, provider contact, business write or main-branch merge.
Source replacement can trigger the existing development server's own reloader;
no independent service restart or hook-cache invalidation is authorized here.

## Acceptance

Exact backend byte equality with reviewed files, preserved unrelated files,
strict OpenSpec, focused offline paired regressions, independently reviewed
preflight and remote backup before installation. No marker assignments may exist
before source changes. Install Restaurant first, then TIX, preserving app order.
Verify disk source, fresh effective hook chain and ordinary bounded HTTP reads.
Do not equate fresh-process hooks or unmarked reads with loaded-worker execution
proof, marked-account denial or full compatibility acceptance.
