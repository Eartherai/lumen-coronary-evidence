# Moderator guide

Do not give this file or the answer key to a participant before the session. Use one neutral moderator where possible. A person who built the app, watched the judging rehearsal, read the answers, or was coached on these tasks can give useful feedback, but must be marked **exposed** and excluded from the independent gate denominator.

## Before the session

- Ask for voluntary agreement to an interface review. Explain any recording separately; screen/audio recording is optional and needs consent. Use a pseudonymous session ID. Do not collect patient data or infer a clinical qualification. Record the person's self-described role and prior exposure.
- Target three independent reviewers, including at least one unfamiliar with ML and one familiar with it if available. Record actual recruitment and experience. Do not fill in absent reviewers or replace a failed session silently.
- Record protocol SHA-256, reviewed source/release manifest SHA-256, date/time, exact app route, device, OS, browser/version, input method, viewport and zoom. Log whether the browser uses integrated or dedicated graphics if actually known. CPU inference is not evidence of GPU-free browser rendering.
- Check the saved model/evaluation bindings in `protocol.json`; if they differ, stop and reconcile the release. UI-only changes require a new reviewed build hash and a new session wave, with original results retained.
- Close this guide, the answer key, developer tools and the judging script on the participant's display. Use the public local Python app or the verified static app and record which. An actual reviewer session must use the same release the submitter intends to publish.

Read this introduction verbatim:

> This is a review of a research interface using public development records. It is not a medical assessment. Please use the interface to complete each task, then tell me your final answer. I can repeat the task but cannot show the solution. You may stop at any time. I will record whether the task was completed, elapsed time, and any confusing wording. Please do not use personal health information.

Allow **45 seconds of unstructured orientation** before T1. Do not identify controls, explain threshold/profile behavior, open a demo preset, or reveal the answers. The UI's normal educational disclaimer stays visible. Allow questions about the session process only. Log any additional explanation as assistance.

## Run the six tasks

Use the order T1–T6. Carryover from this order limits any learning-free interpretation; record it rather than claiming all tasks measure first use. Do not rehearse tasks before measuring. Give only one participant prompt at a time. The exact time limits are in the protocol: T1 120 s, T2 180 s, T3 150 s, T4 150 s, T5 180 s, T6 180 s.

Start the clock immediately after finishing the prompt, once the recorded starting state has finished loading. Loading that occurs after Start counts toward elapsed time. Stop at the person's **first declared final answer**, abandonment, or cap. Do not require continuous think-aloud; it changes task time. Ask for the requested final explanation while the clock is running. Record elapsed time to the nearest second using a monotonic stopwatch and UTC start/end separately.

Record attempted tasks even when they fail. A cap is `timeout`, never a successful time of 0. A device/app fault is `technical_failure`, retained in the attempted denominator and reported separately. Pause only for an external interruption such as a phone call; record pause seconds and reason, plus total wall time and active time. Do not pause for navigation, reading, lag, uncertainty, or wrong turns.

Allowed assistance: repeat the exact prompt on request; explain how to stop the session; fix an unrelated physical setup problem. Log every intervention. Any control-location hint, solution step, model explanation, or answer confirmation makes the task assisted. Assisted completion cannot count as an unassisted success.

For each task, record functional completion and conceptual correctness separately. Preserve the first final answer and any earlier misleading statement. A later coached correction is debrief feedback; it does not upgrade the score. Spontaneous self-corrections are recorded, with the final answer scored against the frozen criteria. Never prompt with questions such as “is that probability actually stenosis?” during a measured task.

## Starting states and resets

| Task | Moderator setup before reading the prompt |
|---|---|
| T1 | Freshly load the app's ordinary landing state. Full profile and training-selected rule. Cohort audit retains its ordinary default LCX/error filters. Do not open the requested record. |
| T2 | Freshly load the same landing state. Training-selected rule. Do not use the shared-miss challenge button for the person. |
| T3 | Open UCI411-057 from the audit, target LCX, full profile. In the audit set all outcomes, any behavior, all folds, ID query UCI411-057. Training-selected rule. Recorded label may be visible because this is an outcome-aware audit. |
| T4 | Open UCI411-128, full profile, LAD, training-selected rule. Original inputs; no editor open. |
| T5 | Open UCI411-128, full profile, LAD, training-selected rule. Reveal the original labels. Confirm Age is 62; no editor open. |
| T6 | Open UCI411-171, full profile, training-selected rule. Choose overall CAD, restore Overview, all vessels visible, shell checkbox recorded, score calculation closed. |

All prepared starting states are part of the design, not participant completion. Record a setup deviation, and do not quietly substitute a favorable case. During T3, audit counts describe all 242 target records even while one record is searched. During T6, a matching anatomy label is permitted; note label versus mesh selection so it is not misreported as successful ray picking.

## After the tasks

Ask “What was confusing?” and “Which part would you check before relying on an output?” without suggesting the expected answers. Only then discuss correct answers. Record proposed fixes as feedback, separate from measured performance.

For the three-person provisional review, report per-task unassisted functional successes/attempts, conceptual successes/attempts, critical misunderstandings and technical failures. Show every eligible session; include assisted/time-limited sessions. Times summarize successful unassisted tasks and also list timeout counts; do not compute a flattering mean after hiding failures. With fewer than three eligible reviewers, state **review incomplete**. With more than three, use every eligible session in the wave and report exact counts rather than selecting the best three.

The gates are project readiness checks, not the official rubric and not clinical validation. A defect can be fixed without retraining. Preserve the original wave, identify the changed UI wording/build, and retest the failing behavior on independent people with a versioned protocol. A human submitter must still complete code/evidence/video review and judging rehearsal.
