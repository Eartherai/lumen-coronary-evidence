# Lumen stale input prediction fix verification — 11 October 2026

The P2 finding in the preserved [initial review](review.md) is resolved in source. A superseded input prediction now suppresses both success and failure results; its handler cannot display an old error or release a button owned by a newer pending case load. Current request failures remain visible and release their own control.

Four new regression tests execute the actual prediction function and click handler in a synthetic fixture. They cover stale rejection after a new case commits, button ownership while a new case is pending, a current rejection, and stale success. The transition suite passed 17 tests. The relevant Node suite passed 52 tests with zero failures. The existing journey checker passed all 64 case/target/rule paths, thresholds, receipt routing, and the nonmonotonic LAD example. JavaScript syntax checking passed.

This is AI source review and software regression verification. It is not a human usability, clinical, field, external-cohort, or fresh actual-browser study. The preserved actual-browser receipt binds the earlier source hash; no claim extends that receipt to this later source. The frozen evaluation, model, and protocol files have their original hashes, with no model refit or rescore. Root owns final commit and R2 release packaging.

Exact current source hashes, commands, and preserved frozen artifact hashes are in [fix-verification.json](fix-verification.json).
