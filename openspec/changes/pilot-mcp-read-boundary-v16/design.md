# Design And Recovery

Use dedicated pilot branches/worktrees from the installed commits; transfer only
the reviewed backend files, not the candidates' full ancestry. Retain existing
README content and minimarket documentation. Stage and push the validated pair,
then use clean detached checkouts at exact pilot commits in the installed apps.
No maintenance ref is advanced. The external MCP retains its pinned source.

Before checkout, use a protected read-only inventory: Frappe/ERPNext major 16,
current installed source hashes/cleanliness, installed app order, marker Role and
Has Role counts (including orphan rows), actual current auth hooks/cache mode,
and projected candidate callback composition. Fail on any marker assignment,
source drift, unknown auth composition or unresolved review blocker. No secret,
account identity, session payload or provider credential belongs in evidence.

Read checks have bounded timeouts, no redirects/retries, static allowlisted GET
routes and no body. Existing credentials may be consumed only in memory for this
runtime operation, never printed or copied into the repository. Prefer local
HTTP transport to avoid sending the credentials across the LAN. Do not retry the
previously hung native MCP call. Record failures, not inferred success.

Install the optional Restaurant bridge first: absent TIX finalizers is no-op.
Install TIX second only after repeating the marker/clean-source preconditions.
No role is created or assigned, so the account remains unmarked. Fresh-process
hook reconstruction and HTTP availability are separate evidence; without an
approved worker reload or marker test, loaded-worker coverage is not certified.

Recovery before activation: if either checkout/check fails, stop and inspect;
restore only the clean pilot checkouts to the recorded original commits/branches
within this code-only pilot, preserving any concurrent user changes. Do not use
reset/clean, delete branches, restore DB/configuration, remove marker roles,
change services or treat a failed post-check as permission to expand scope.
A mixed pair is not acceptable for marked accounts. Recheck marker counts first.
No data migration or business-document rollback is applicable.
