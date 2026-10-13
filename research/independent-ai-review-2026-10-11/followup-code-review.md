# Follow-up code review — outcome fixes and runtime instrumentation

This is a read-only source/test audit of root's instrumented source revision, separate from the earlier actual-browser review of the Oct 10 static baseline. No browser was opened or operated during this follow-up, and no post-fix browser verification is claimed. No core source was edited. Frozen model, cohort, split, evaluation and protocol-bound artifact hashes still match the earlier checks; no fitting, outcome-evaluation script or holdout rescore was run.

The audited file hashes are recorded in [followup-code-snapshot.json](/Users/earther/Desktop/IIT%20mandi/coronary-evidence/research/independent-ai-review-2026-10-11/followup-code-snapshot.json). The probe edge reproduction used `runtime-probe.js` SHA-256 `d531d64365f13aa89b2d3b1f29250d428216fea766891df243c552d507904337`. Later edits need separate verification.

## Remaining findings

### [P2] The sample deadline depends on successful rendering callbacks

The duration check exists only in [runtime-probe.js:55](/Users/earther/Desktop/IIT%20mandi/coronary-evidence/public/runtime-probe.js:55). `start()` records a requested duration but schedules no independent finish. In a Node module reproduction, `start(1)` followed by a real 1,102.5 ms wait with no `frame()` call still had `active: true`, zero frames and no finish reason. The exposed 1-second API duration uses the same termination path as the UI's 10-second duration.

The application can reach this condition when anatomy/WebGL initialization fails before the animation loop starts, or when a render callback stops reaching the probe. The panel is mounted independently of `buildAnatomy()` success. A hidden/no-callback period can also prolong capture. Export stays disabled until a subsequent successful frame or a manual Stop. The advertised sample duration is therefore not bounded by elapsed time on the failure path.

Expected behavior: finish automatically at the requested elapsed deadline, report the actual duration, and preserve an invalid/insufficient-frame status when rendering failed or visibility changed. A timer/watchdog should be cleared on finish/restart, and finishing should be idempotent so a late callback or Stop cannot overwrite the original endpoint. Add a no-frame deadline test; retain the existing visibility invalidation test. This finding concerns the diagnostic's reliability, not model predictions or GPU-free rendering performance.

### [P2] Failed, superseded and unfinished actions silently disappear from the sample

`begin()` stores an operation only in `tokens` ([runtime-probe.js:39](/Users/earther/Desktop/IIT%20mandi/coronary-evidence/public/runtime-probe.js:39)). It is added to exported `capture.operations` only by a successful `end()` while the capture is active ([runtime-probe.js:44](/Users/earther/Desktop/IIT%20mandi/coronary-evidence/public/runtime-probe.js:44)). `finish()` does not serialize tokens that have no endpoint. The application's case-load and recalculation paths can throw, return after a version guard, or finish after the sample deadline without calling a successful endpoint.

A deterministic reproduction began `case_or_profile_load`, recorded two frames, and automatically finished at 1,001 ms before the action ended. The sample had `status: measured` and `operations: []`. A later `end()` at 1,200 ms left it empty. This proves an in-flight action vanishes rather than appearing as incomplete/censored. A failed or superseded action likewise never appears because the app calls `runtimeProbe.end()` only on the successful path.

Consequence: a reader cannot distinguish no attempted interactions from attempted slow/failed/superseded interactions. Latency summaries made from the export can omit the worst experiences without an attempted-action denominator. This does not establish that root's captured successful-action measurements are wrong; it limits what an export can claim about all attempted interactions.

Expected behavior: retain an operation at begin and give it an explicit completed, failed, superseded or unfinished-at-sample-end status. Record only public identifiers and sanitized status codes; no raw clinical inputs or error payloads are needed. Preserve null endpoints or a lower-bound elapsed value for incomplete actions, and summarize completed latency separately from failure/incomplete counts. A smaller alternative is to disclose that only completed successful actions are recorded, while exporting attempted/omitted counts. Add tests for an unfinished action at capture end, rejected load, and version-cancelled load.

Reproduction evidence for both findings: [runtime-edge-reproduction.json](/Users/earther/Desktop/IIT%20mandi/coronary-evidence/research/independent-ai-review-2026-10-11/runtime-edge-reproduction.json). These are module/source results, not browser observations or human task times.

## Fix assessment and tests

The outcome helper applies the same `probability >= threshold` rule as the visible flags and correctly distinguishes both disagreement directions. Finite values, valid binary truth and equality at the cutoff are checked. `renderTruth()` now uses this helper with the current shared decision mode. The prior false-alarm finding is addressed at source/unit-test level.

`loadCase()` now clears `tour-note` after the version guard and committed current-case replacement. This addresses the earlier stale-notice sequence at source level, while audit selection provenance remains in `case-caption` and `openAuditCase()` can set a notice for the current audit case. The browser transition itself is being verified by root separately.

Executed `node --test coronary-evidence/tests/test_runtime_probe.mjs coronary-evidence/tests/test_outcome_description.mjs`: **8 tests passed, 0 failed**. They cover both mismatch directions, matching predictions, threshold switching on the saved development example, cutoff equality, invalid outcome values, observed-interval rate calculation, distinct DOM/render endpoints, clinical-value stripping, visibility invalidation, duration-argument validation and restart token isolation. They do not cover the two lifecycle findings above. Test output times are software test metadata, not human usability evidence.

## Privacy and measurement interpretation

No sensitive-data transmission, clinical-value persistence or prediction/outcome collection was found in the audited instrumentation. The app passes public case/profile/target identifiers; the probe filters metadata to those identifier keys. Browser/viewport/WebGL environment is collected locally, and exporting JSON requires the explicit diagnostic control. The diagnostic does not add network calls, local storage or a remote telemetry destination. Generic custom environment callbacks should remain restricted if this module is reused.

The frame summary derives callback rate from observed timestamps, not an assumed monitor refresh rate. Hidden transitions invalidate foreground interpretation. The scope correctly disclaims GPU completion and physical display latency. An idle sample only describes idle behavior on that browser/device; responsiveness during interaction requires interaction samples and cannot establish broad browser/device coverage.

One measurement-boundary clarification remains useful: in `app.js` the CPU timer encloses controls, Three.js render submission and vessel-label updates, then stops **before** `runtimeProbe.frame()` and its periodic panel/status updates. The `callback_cpu_ms` field therefore excludes the instrumentation itself, even though the observed callback intervals include its overhead. Describe it as render/label work duration or state the timer boundary when reporting it; do not call it total event-loop or total callback CPU time. This is an interpretation limit, not a separately established P1/P2 failure.

No P1 defect was established in this follow-up. The two remaining P2 findings concern diagnostic lifecycle/completeness. Human review/signoff and clinical validation remain pending, and this code audit does not upgrade the earlier browser evidence to a new release verification.


Parent implementation follow-up: the delegated agent completed timer/unfinished-action changes and allowlisted graphics-context invalidation with regression checks (19 outcome/runtime checks total). The parent separated anatomy errors from case errors, guards lost contexts before recording render submissions, and preserves a concrete rendering failure from the first-frame watchdog. These app edits are parent work, not a claim of a subsequent independent browser or human review.
