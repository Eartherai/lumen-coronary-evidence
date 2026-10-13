# Remaining robustness audit and fixes

Reviewed baseline: `c8868fc37f58c8e2ca9c6ab41ba12a68c6791c84`.
Reviewer kind: AI code audit. No browser automation, human study, patient inference, model training, or final-holdout reads were performed by this reviewer.

## P2 — A failed selection could leave the requested profile attached to the previous score

Before the fix, profile callbacks assigned `activeProfile` before loading. `loadCase` protected successful commits with `caseVersion`, but did not restore the selection on a current failure. A synthetic failure selecting NEW/history retained OLD/full predictions while the case selector showed NEW, the profile selector showed history, and `activeProfile` was history. The displayed original caption remained OLD. Selecting another target would rerender the comparison using the uncommitted history highlight.

An older rejected request also escaped to `.catch(fail)` after a newer case had successfully loaded. It could display a stale failure over the successful current case. The baseline source hash and exact synthetic observations are in `async-state-evidence.json`. Transient endpoint failure is most directly relevant to the supported local Python API: the static deployment caches its public bundle and normally computes these later routes locally.

The fix passes requested profile and optional target to `loadCase` without mutating committed identity. After every response arrives, one current request commits case/profile/target together. A current failure restores both selectors to the still-displayed case, including restoring the previous dynamic audit option. A superseded request returns `false`; it cannot display an old error or release controls owned by a newer request. Audit and tour callers stop when loading did not commit. Pending loading has a visible notice that identifies the estimates still on screen. Returning to the committed profile while a different matrix profile is pending starts a superseding request.

Recorded-label requests now discard stale rejections as well as stale successful responses. Errors for the current record still reach the visible error handler.

## P2 — Selecting a prediction removed keyboard focus

`selectTarget` calls `renderPredictions`, which replaces all prediction cards with `innerHTML`. The focused card was removed from the document on every activation. The parent independently observed `document.activeElement` become BODY after choosing LAD in the browser before this patch. This reviewer verified the source path and supplied the bounded fix; no browser fix claim is made here.

The prediction grid captures a focused target only when focus is inside that grid and restores focus to its replacement button with `preventScroll`. Rendering while an outside input or control is focused does not steal focus. The parent owns the corresponding comparison-matrix change and its browser checks.

## Validation completed here

`node --check public/app.js` passed. `node --test tests/test_case_transition.mjs` passed all 13 tests. These execute the actual app transition functions against synthetic delayed API responses and minimal DOM fixtures. They cover failure rollback, audit-option rollback, stale success/failure ownership, pending loading status, case/profile/target commit, stale label replies, returning to the committed matrix profile, focus retention and avoiding outside-focus theft. This is software regression evidence, not a human completion rate or measured browser latency.

Changed code: `public/app.js`. New tests: `tests/test_case_transition.mjs`. The parent adds `#case-load-status` in `public/index.html` and performs actual browser verification. No scientific artifact, model, explanation certificate, split, final score, or threshold changed.
