# Lumen: independent human review kit

Prepared 11 October 2026. **Protocol ready; human sessions and human signoff pending.** No reviewer has been invented and no usability result is claimed by this kit.

Use this kit to find interface misunderstandings before submission. It tests whether a person can inspect the existing research evidence. It does not test clinical decision making, diagnostic accuracy, health outcomes, clinical trust, or medical usefulness.

1. A moderator reads [the protocol](protocol.json), [moderator guide](moderator-guide.md) and [answer key](answer-key.json) privately. Freeze the protocol hash and actual reviewed build before the first session.
2. Give the person only [participant tasks](participant-tasks.md). Allow the standard introduction and the same starting state for every person. Do not demonstrate the answers first.
3. Record each real session using a copy of [session-template.json](session-template.json). Keep first final answers, timeouts, technical failures, and verbatim misunderstandings. No answer feedback until all six tasks finish.
4. Apply the provisional gates in the protocol, report exact numerators and denominators, and fix specific defects. A small convenience sample is formative feedback; it cannot establish a population-level usability claim.
5. Separately rehearse the [seven-minute judging walkthrough](judging-walkthrough.md), review [current judge answers](judge-qa.md), and complete [human signoff](human-signoff.md). A rehearsed submitter is not an independent reviewer.

The optional [orientation comparison](baseline-orientation.md) has its own freeze and is **not ready to run until genuine baseline captures and their answer regions have been prepared**. It must not be described as a clinical or causal validation study.

Core tasks use the complete 242-record development audit. The 61-record final holdout remains separate. The source-bound answer key reads saved artifacts; the kit neither retrains models nor rescores the holdout. Human review does not authorize changing frozen weights, thresholds, or evaluation outcomes.

The supplied [Track A extract](../../../research/source-extracts/Track%20A.txt) assigns 30% to predictive performance, 25% to 3D visualization, 20% to interpretability, 15% to integration, and 10% to implementation. This kit addresses clarity and integration evidence; it does not manufacture rubric scores. The source rules are a supplied snapshot, not a new live deadline verification.

Actual human identity, eligibility, GitHub/YouTube URLs, and submission status stay in the existing publication handoff. This kit does not infer or publish them. It contains no external messaging or account actions.
