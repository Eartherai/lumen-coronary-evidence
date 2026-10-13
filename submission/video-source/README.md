# Lumen submission demonstration

This is the complete renderable source for the 5m42.83s English demo in `../../output/video/lumen-demo.mp4`. It contains the actual recorded application clips, final captured stills, local narration audio and deterministic HTML/GSAP compositions. Capture action logs preserve the actual interaction sequence. Raw screencast JPEG frames remain in the original working folder; these encoded clips are the frozen source media used in the film.

Install Node.js 22+ and FFmpeg, then run from this folder:

```sh
npm ci
python3 extend_with_audit.py
npx hyperframes@0.8.143 check
npx hyperframes@0.8.143 preview --background
npx hyperframes@0.8.143 render --quality delivery --fps 24 --workers 2 --output renders/lumen-demo.mp4
```

The generated English narration is already bundled; a model download is not required to rerender. It was produced with Kokoro ONNX 0.6.1, local Kokoro-82M weights, `af_heart` at speed 0.93. This is generated speech and does not claim a human narrator. No cloud rendering or paid provider was used. The application clips were captured through actual CUA browser interaction at 1280×1000, played at their original speed and then held on their last captured frame. Informational callouts are not verbatim subtitles.

The custom composition source follows the project MIT license; third-party software remains under its own terms. GSAP 3.14.2 is Copyright 2025 GreenSock/Webflow, under the [GSAP Standard License](https://gsap.com/standard-license/); its bundled file retains the original notice. HyperFrames 0.8.143 and the retained catalog component use [Apache-2.0](https://github.com/heygen-com/hyperframes/blob/main/LICENSE), Copyright 2026 HeyGen, Inc.; the full license and adaptation notice are included in `licenses/`. The Kokoro model is [Apache-2.0](https://huggingface.co/hexgrad/Kokoro-82M); model weights are not bundled here. The anatomy and source dataset shown in the film are credited in the parent project's THIRD_PARTY_NOTICES.md.

`video-qa.json` records media metadata, SHA-256, clean composition gates and source-to-encoded narration alignment for every chapter.

The added 62.361-second opening uses two actual1280x720 CUA static captures, clearly labelled in the film, and a bundled60.361-second local narration recording. The total film is342.833333seconds. `check-audit.json` is the current composition check; `check.json` is the preserved original six-chapter check. `verify_audit_video.py` checks encoding and all seven narration alignments and extracts final frames; visual inspection is recorded separately in the QA receipt. Captured clips were reencoded with dense keyframes without changing their speed/content; receipt in `assets/dense-keyframe-receipt.json`.
