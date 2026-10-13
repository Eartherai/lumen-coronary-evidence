# Lumen interface redesign

The user rejected the interface and requested UI/UX Pro Max, Anthropic Frontend Design and Taste. This is a working research instrument for judges and technical reviewers, rather than a marketing site. The existing HTML/JavaScript and Three.js runtime remain the implementation stack.

The memorable element is the actual interactive heart, large enough to inspect on a laptop. The chrome around it is light and calm. Clinical-looking presentation must not imply a validated diagnostic instrument.

## Direction

- Background: cool cloud `#f3f6f8`; main surfaces: white `#ffffff`.
- Main ink: deep navy `#193342`; secondary ink: slate `#536775`.
- Primary action: deep teal `#126e68`; error/false-alarm emphasis: rust `#a74c30`.
- Anatomy stage: navy `#102633`; stage text uses a separate high-contrast light palette.
- Typeface: Figtree, self-hosted with a system sans fallback; one family with differentiated size/weight, tabular numerals for model values.
- Shape hierarchy: 16px workspace surfaces, 10px inputs/buttons, compact status labels. Minimal shadows; structural borders only where they separate functions.
- Motion: short state feedback, no decorative scroll choreography. Respect reduced motion.

## Layout

Compact brand/navigation and an always-visible educational notice lead into a short left-aligned title and one audit action. The desktop workspace has a narrow case/input rail, a dominant anatomy stage with four target selectors, and a score/explanation rail. Each panel keeps its own natural height, rather than stretching to the longest content. On tablets the input rail sits alongside the anatomy and the evidence becomes one full-width section; on phones the input controls precede anatomy and evidence in reading order.

```
Lumen     Case explorer / Compare inputs / Cohort audit / Model evidence
Educational research notice
Make every prediction inspectable.                    Open cohort audit
Case / inputs       Interactive reference anatomy       Selected estimate
Recorded values     Four target predictions             Contributions
                     Decision rule                      Recorded labels
Compare profiles
Complete development audit
Development evidence / frozen test
```

## Skill application

UI/UX Pro Max's data-density and Three.js container-sizing guidance fits the application. Its generated Enterprise Gateway/Portfolio Grid landing recommendations and serif/code display-font suggestions do not fit this working instrument and were rejected. The direction above is an authored application-specific choice, not a fully matched database template. Anthropic's guidance supplies restrained typography, subject-specific composition and honest copy. Taste is explicitly scoped away from dashboards; only its contextual redesign restraint and anti-default checks are used here, without migrating this existing app to React or imposing its landing-page checklist.

## Contracts and validation

Preserve every JavaScript-bound ID, original model/label separation, cohort/profile loading and case-transition protections. Keep shell-toggle and vessel-labels inside viewer. Adapt generated SVG text to the new palette. Keep scientific inputs/models/thresholds/evaluation unchanged. Verify original interaction tests and actual browser behavior at desktop, tablet and mobile widths, including cohort inspection, profile selection, recorded-label reveal, edited-input guard, navigation, readable charts and page overflow. Existing submission archives remain historical until a separately verified redesigned delivery is prepared.
