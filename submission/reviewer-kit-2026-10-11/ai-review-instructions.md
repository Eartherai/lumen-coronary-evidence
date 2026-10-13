# Independent AI review using the frozen task contract

An AI review is authorized separately from the human protocol. Use `reviewer_kind: "ai"` and [ai-review-template.json](ai-review-template.json). It can supply technical/UI findings and challenge claims; it **cannot** supply human reviewers, human completion times, human understanding scores, or human signoff. Never pool it with `session-template.json` results or the provisional human usability gates.

The task prompts, source-bound expectations and critical misunderstanding criteria are useful adversarial checks. Attempt T1–T6 against the exact reviewed build and distinguish:

- `browser_observed`: personally operated the current UI and captured evidence of the actual behavior.
- `source_verified`: inspected the relevant source/artifacts without observing that UI behavior.
- `not_tested`: no sufficient evidence. Do not upgrade this to passed from an expected answer.

Record the starting build manifest hash, protocol hash, tool path, browser/device if used, and exact scope. Keep screenshots or browser event records as evidence references if created by the actual run. An agent can inspect the answer key; it must not imply a blinded or uncoached user session. AI execution durations, if recorded, are tool/runtime metadata and not human task times.

Review task fidelity, data/model identity, flag/filter consistency, explanation reconstruction, label separation after edit, anatomy-to-target mapping, loading/error states, accessibility, wording and disclosure. Review code for substantive defects as well: race/stale-state behavior, mismatched thresholds, truth entering inference, hidden full-input assumptions, nonfinite/unknown-input handling, privacy/persistence, and release/reproduction gaps. Confirm any suspected defect against source or an actual browser run before declaring it.

For each finding state the trigger, observed or source-proven behavior, user consequence, file/line or artifact reference, reproduction steps, and a bounded fix. Assign severity based on the actual consequence; do not invent clinical outcomes. Separate facts from interpretation. Report no findings when appropriate; never manufacture a failure to make the review look independent.

Conclude with scope-qualified task statuses and unresolved limitations. Human review remains pending regardless of whether all AI task checks pass. Do not mark the frozen model/evaluation changed or rescore the final holdout to improve a result.
