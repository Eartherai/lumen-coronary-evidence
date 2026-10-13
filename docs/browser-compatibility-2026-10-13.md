# Browser rendering correction - 13 October 2026

The exported interface could load scores in native Safari while the heart
remained blank: the first frame depended on an animation callback that did not
arrive during the observed check. The same earlier export and its watchdog
message are retained in the dated browser evidence.

The current application submits a real WebGL frame immediately after loading
geometry and after camera, vessel, isolation, surface and resize changes.
Named labels are projected in the same completed draw. Animation callbacks
still support damping and the opt-in runtime diagnostic. Input-triggered draws
are not counted as animation callbacks or used to claim frame rates.
Context loss cannot report success; draw failure stops further rendering and
keeps an explicit failure visible.

Seven callback-contract tests cover immediate completion, lost context and
recovery, drawing/acknowledgment exceptions, reentry and stopped state. A clean
29-payload portable build was checked through native Safari and the Codex
Chromium browser on this one Mac. The native Safari screenshots show the
rendered heart, correctly projected labels, selected LCX, actual isolated mesh,
focus/opposite views and the UCI411-020 missed-positive audit. An earlier
experimental tab reused cached modules; its screenshots are retained as
preliminary attempts and are not the release pass.

This is an AI-operated browser check, not a first-time human review, a second
physical laptop, a Safari frame-rate benchmark or a clinical validation result.
Models, thresholds, all four frozen final-test metrics and recorded outcomes
are unchanged. The 12 October six-page report and 3:52.75 film retain the source
version bound in their original provenance; this later code correction does not
rewrite their records or assert a new scientific experiment.

Evidence: [source-bound browser receipt](../research/browser-compatibility-2026-10-12/release-verification.json).
The old source/static exports remain dated historical artifacts. Use the final
13 October package's source and browser build for local execution.
