# Contribution review test coverage follow-up

Date: 2026-11-09. Contract and cases: [private/public memory review tests](../test/memory-community-smoke-v1.md).

## Root cause

The review implementation checks descriptive fields beyond `summary`, but the main adversarial marker loop exercised only `summary`. Existing focused tests touched an attribution author and section markup, yet did not prove every public text field produced a field-specific fixed-code finding with no matched value in the report. Card detection had a positive example but no Luhn-invalid negative control.

## Design

Add a core test matrix placing one synthetic AWS-shaped marker in `title`, `summary`, `author`, `sections[0]`, `tags[0]`, `origin.author`, and `attributions[0].author`. Each value fits the field's length limit. Assert a blocked verdict, the exact `R1/aws_access_key` finding path, and serialized-report redaction.

Add a route-level case with the marker in a submitted tag. Use a real Router and temporary SQLite file. Independently inspect the review response, the still-pending owner contribution, anonymous 404, and absence of a catalog row after the rejected approval. A card-like string with a failed Luhn checksum remains the negative control.

## Review

No production behavior changed. The new tests pass against the current core and HTTP path. The route case confirms the public boundary as well as the pure review function.

The latest full workspace run passes. A separate code-review finding remains in the active issue #402 work: `http/admin.rs::authorize` is unused, while `http/account.rs::admin` accepts only the operator Bearer token. An allowlisted email administrator session therefore cannot use the contribution queue or decision routes, despite the #402 contract. The compiler reports the unused helper. This was left for the session that owns #402; the review route needs a session-based regression test.
