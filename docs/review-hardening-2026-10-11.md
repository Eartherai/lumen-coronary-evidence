# Independent AI review and release hardening — 11 October 2026

The user requested an agent review. A fresh AI reviewer exercised Lumen's evidence loop and found two P2 defects in record provenance and error wording. Both have been corrected in the canonical source. This work improves the interface's interpretation of existing evidence; it does not change frozen model weights, thresholds, the 242/61 split, or the once-only final evaluation.

This document distinguishes the independent review of the prior build, current source checks, and later root browser verification. **Human usability and human release signoff remain unmeasured/pending.** An AI review is not a clinical review or external validation, and supplies no competition ranking or win probability.

## What the independent agent actually reviewed

The reviewer first read [the six participant tasks](../submission/reviewer-kit-2026-10-11/participant-tasks.md), then tried them in an actual hidden Codex in-app browser before reading the moderator guide, answer key, implementation, rubric or prior review material. It used the Oct 10 static baseline at `http://127.0.0.1:8770/`, with 1280 × 720 screenshots. The report is [review.md](../research/independent-ai-review-2026-10-11/review.md), with [machine-readable assessments](../research/independent-ai-review-2026-10-11/ai-review.json).

The starting build hash and exact start time were not captured before interaction. Root later bound the session retrospectively to the unchanged static baseline and verified all 23 manifest-listed files. That manifest's SHA-256 is `85473965f569433aec400fc4db876528ada061c55bc8963ca20c7ba4b0b74463`; the task protocol SHA-256 is `8ba0a8b84661e5a2a43157fff47272a227a2cd7c2329eba372597693e5fa1d39`. Later canonical-source fixes were not served during that independent run. This distinction preserves the original findings rather than presenting them as a review of a patched build.

| Task | Observed scope |
|---|---|
| T1, arbitrary record | UCI411-276 was found in all 242 development records and opened; LAD 22.5% at 39.0% correctly matched a negative recorded label. |
| T2, shared LCX error | The challenge filter returned nine shared misses; UCI411-020 showed positive truth and five negative flags. The reviewer correctly distinguished the whole-cohort 60/172 agreement-error count. Prior task state was retained rather than a fresh reset; the challenge reset filters. |
| T3, decision rule | UCI411-057 remained 43.9%; its flag changed from positive at 31.0% to negative at 50.0%. Whole-cohort LCX FN/FP changed 17/82 → 63/18. Probability was browser observed as unchanged; contribution/color/weight invariance was source verified. |
| T4, input profiles | UCI411-128 LAD flags were positive/negative/negative/negative/positive. Examination and full cells synchronized the explorer, input count, probability and explanation. The task's “All measurements” wording differs from the UI's exact “All recorded inputs (+ echo)” label. |
| T5, edited inputs | Age 62 → 63 changed LAD 44.4% → 45.4%; truth was hidden, reveal disabled and the original profile comparison paused. Restoration and a fresh reveal returned the original comparison. |
| T6, anatomy and score | Anatomy-label selection, rotation/zoom, Overview and the 0.569 + 2.248 = 2.817 log-odds calculation giving 94.4% were observed. Focus/isolate commands were invoked, but a later locator error discarded that call's screenshot output; isolated rendering was not independently retained or visually judged. Its control logic was source verified. Mesh ray picking was not tested. |

These are AI task observations, not six independent people or human task success rates. The agent saw all prompts together and prepared some starting states itself; no neutral human moderator took part. Automation locator recoveries are tool-path events, not measured human obstacles. Browser version, device, graphics renderer and FPS were not measured in that independent run. Malformed-input, race, keyboard-only, offline/loading-failure and reduced-motion scenarios were source reviewed or left untested, as stated in the report. The saved actual-SHAP certificate was inspected, not rerun. No final-test rescore occurred.

## Two bounded fixes

**AI-20261011-01: stale audit provenance (P2).** After opening audit UCI411-057 and then ordinary UCI411-128, the old hero notice still named UCI411-057 even though the score and selected record correctly changed. [`loadCase` in app.js](../public/app.js) now clears the contextual notice when a new case/profile load commits. Audit and tour entry points can then set a notice for their actual current record. This repairs conflicting identity/provenance; the baseline review did not establish inference misrouting.

**AI-20261011-02: false alarms described as misses (P2).** UCI411-128 full LCX had a positive flag at a 35% threshold against a negative recorded label, but its revealed row said “prediction missed.” [`outcome-description.js`](../public/outcome-description.js) now derives wording from the current probability, exact displayed cutoff and truth: `false alarm` for predicted positive/truth negative, `missed positive` for predicted negative/truth positive, and `agrees` for a match. The reveal uses the same selected decision rule as the rest of the explorer.

The initial eight targeted Node checks for [outcome descriptions](../tests/test_outcome_description.mjs) and [runtime probe behavior](../tests/test_runtime_probe.mjs) passed during this documentation pass. They cover both mismatch directions, correct states, an actual UCI411-128 threshold change, cutoff equality, invalid values, measured frame intervals, distinct latency endpoints, stripped clinical metadata, visibility invalidation and sample isolation. These tests do not establish complete post-fix browser behavior.

Root's [post-fix UI receipt](../research/runtime-2026-10-11/review-fix-ui-receipt.json) records opening UCI411-057 from the audit, changing to UCI411-128, and observing the old notice hidden with empty text. The same browser showed LCX UCI411-128 `Negative label · false alarm`, with 42.2% at the learned 35% cutoff. [Screenshot](../research/runtime-2026-10-11/corrected-case.png).

The [390 × 844 responsive check](../research/runtime-2026-10-11/responsive-390.json) recorded document and page scroll widths of 390 pixels, a 360 × 360 anatomy canvas, and `Only the LCX reference vessel is visible` after focus/isolation. [Actual narrow screenshot](../research/runtime-2026-10-11/narrow-isolated-lcx.png). The override was reset and all reference vessels restored. This later parent check adds evidence beyond the independent task T6 limitation; it does not alter that review's historical record or establish physical phone/device testing.

The [Safari attempt](../research/runtime-2026-10-11/safari-attempt.json) loaded scores and controls, but anatomy stayed blank and the sample had zero callbacks. Native coordinate focus could not establish an available foreground window while AX observations remained usable. The invalid sample was stopped; an unexpected download permission was cancelled. The root cause remains unresolved. No Safari frame-rate or complete engine pass is claimed.

## What the measured runtime sample establishes

The current build has an opt-in local diagnostic in [`runtime-probe.js`](../public/runtime-probe.js). It records foreground animation callbacks, main-thread callback CPU time, action-to-DOM-update time, and action-to-next-completed-render-callback time. Captures invalidate foreground FPS when document visibility changes. Metadata is limited to operation names and public case/profile/target identifiers; entered measurements, probabilities and recorded outcomes are excluded.

Root's current instrumented static app was served locally at `http://127.0.0.1:8776/`, separately from the reviewed Oct 10 baseline. Two actual ten-second samples use the same Apple M5 host, Chromium's reported Chrome/155.0.0.0 user agent, an Apple M5 ANGLE Metal renderer, 683 × 760 CSS pixels, device-pixel ratio 2 and 102,802 anatomy triangles. The user-agent `MacIntel`/OS compatibility strings are not independently verified hardware or OS-version claims. Both captures retained visible document state with zero hidden transitions.

| Sample | Render callbacks | Observed callback span | Callback rate | Median / p95 interval | Largest interval |
|---|---:|---:|---:|---:|---:|
| [Chromium idle](../research/runtime-2026-10-11/chromium-idle.json) | 588 | 9,985.4 ms | 58.79/s | 16.70 / 20.57 ms | 202.60 ms |
| [Chromium actions](../research/runtime-2026-10-11/chromium-actions.json) | 586 | 9,984.2 ms | 58.59/s | 16.70 / 18.08 ms | 264.20 ms |

The action sample contains **eight completed operations**: three target selections, three case/profile loads and two decision-rule changes. Their action-to-DOM-update times range from 6.9 to 19.7 ms (median 12.0 ms); action-to-next-render-callback times range from 12.3 to 30.3 ms. These are observed local action endpoints in a small, already loaded workflow. No input recalculation, cold start, network deployment, representative device population, or sustained heavy-interaction benchmark is represented by those eight operations. The captures also contain long callback intervals, so the average rate does not mean every frame arrived at 60 Hz.

The approximately **58.6 callbacks/s** action result measures software scheduling and render submission on this device/viewport. It is not GPU-completion timing, physical-display frame rate, motion-to-photon latency, human perceived responsiveness, GPU-free rendering, or human usability evidence. CPU model training/inference and absence of a paid hosted inference API are separate implementation facts. A modern integrated Apple M5 renderer does not establish performance on older or dedicated-GPU-free hardware generally. The responsive check and unpassed Safari attempt are recorded separately above.

## External validity remains a separate admission problem

The [bounded independent-cohort search](../research/lumen-external-cohort-2026-10-11/README.md) admitted no cohort for external validation of the frozen 55-input, four-target models. AngioCAD was independently collected in origin but its inspected clinical headers lack every required examination and ECG input. Other screened sources reused the original records, lacked the full feature/endpoint contract, or were unavailable within the authorized scope. This is a documented negative compatibility result, not proof that no eligible dataset exists.

No model fitting, adaptation, calibration, threshold tuning or external scoring was performed in that search. Whole missing groups were not fabricated or imputed to create a validation claim. A possible new reduced Age/Sex historical experiment is separately documented with an unresolved endpoint boundary difference; it is not external validation of the shipped model. The current prediction evidence remains the preserved small, single-source internal evaluation, with frozen held-out LCX/RCA false-positive costs and no external or prospective clinical validation.

The independent AI review, bounded code fixes and local measurements can support a more inspectable submission. Real human code/evidence/video review, judging responsibility, eligible team/account fields and verified publication/submission records remain separate pending human actions.


## Final diagnostic implementation and captured build

The final probe ends through an independent timer even if the render loop stalls. Every begun action remains in the export, including pending DOM work and DOM-completed actions without a later render callback, with explicit incomplete status and null unavailable endpoints. Hidden captures, fewer than two callbacks, graphics-context loss and leading/trailing gaps greater than 250 ms invalidate the foreground-rate field. Raw observations remain available. Nineteen targeted outcome/runtime checks passed, including injected timer/stall/context-loss tests; these are software tests.

The [final actual Chromium capture](../research/runtime-2026-10-11/chromium-actions-final.json) completed automatically after 10,000.8 ms, with zero hidden transitions, no context loss, 9.0/7.0 ms leading/trailing gaps, 587 callbacks, 58.69 callbacks/s, and all eight begun actions completed. DOM endpoints were 4.1–12.4 ms; the largest callback interval was 152.7 ms. The earlier samples remain in this dossier and the six-page report as dated measurements; no run was discarded to select an attractive score. [Exact final summary and retrospective site binding](../research/runtime-2026-10-11/final-summary.json).

Callback CPU fields enclose controls, render submission and label updates, ending before the probe and periodic panel updates. They measure that work boundary, not total event-loop CPU time. All captures are short warm local samples on one Mac and an AI-operated workflow.
