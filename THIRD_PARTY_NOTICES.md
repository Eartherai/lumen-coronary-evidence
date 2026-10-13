# Third-party sources and attribution

## UCI dataset

Extension of Z-Alizadeh Sani dataset, UCI Machine Learning Repository, dataset 411. CC Attribution 4.0 International. Data source: https://archive.ics.uci.edu/dataset/411/extention+of+z+alizadeh+sani+dataset . The original archive download and its SHA-256 are recorded in `training/download.json`; the extracted workbook SHA-256 is recorded in `training/results/split.json`. Original labels and source category spelling were retained. Derived development predictions and portable coefficients were computed for this project.

## BodyParts3D

BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.

Official license: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html . Official archive: https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_BP3D_4.0_obj_99.zip . Mesh part identifiers, FMA concepts and individual file hashes are recorded in `public/assets/anatomy-provenance.json`.

Changes: official PARTOF members for heart, LAD, LCX and RCA were merged into exclusive display groups, polygon faces triangulated, coordinates rounded to four decimal places, geometry translated to a shared origin and rotated for browser viewing. Normals were computed in Three.js. No patient-specific geometry, lesions or anatomy were generated.

## Software

Three.js 0.186.1: MIT license, https://github.com/mrdoob/three.js . Its license is included with the installed npm package. NumPy, pandas, SciPy and scikit-learn use BSD-family licenses; joblib uses BSD; openpyxl uses MIT. Consult the exact distributions referenced in `requirements-training.txt` for their license texts. Python is used under the PSF license. Historical interface assets used Google Fonts DM Sans and Manrope with system-font fallback; their font distributions use SIL Open Font License.

The redesigned application uses a locally served Figtree Latin variable font (normal, weights 400–800), Copyright 2022 The Figtree Project Authors, under SIL Open Font License 1.1. Its font file and license are included in `public/assets/fonts/`. Exact official source URLs and hashes are in `research/ui-redesign-2026-10-11/font-provenance.json`. Historical application/video captures may show earlier typefaces.

## AI assistance

OpenAI Codex assisted with track assessment, software implementation, CPU experiments, tests, anatomical integration and documentation. Human submitters are responsible for reviewing the results, disclosures and claims, and explaining the system during judging. AI tools are not human team members. Add the AI tools actually used to Devpost Built With, as required by the hackathon rules: https://multimodal-ai-hackathon-2026-7.devpost.com/rules .

## Demonstration video

The video uses real local application screencasts. English narration is generated locally with Kokoro ONNX (af_heart voice), an Apache-2.0 model, and is disclosed as generated. HyperFrames 0.8.134 (Apache-2.0, Copyright 2026 HeyGen, Inc.) assembles the scenes; GSAP 3.14.2 supplies deterministic animation under the GSAP Standard License. Source package notices are retained under `submission/video-source/`. No paid stock footage, patient-specific imagery or human narration is claimed.

## Current public presentation edition

The 3:52.75 redesigned demo at `docs/submission/lumen-demo.mp4` was rendered with HyperFrames 0.8.148. It uses the same GSAP 3.14.2 licensed animation library and disclosed synthetic Kokoro English narration. Its source provenance and delivery/encoded receipts are retained beside it. The preceding video notice and `submission/video-source/` describe earlier dated editions; they do not bind this newer film. Anatomy/dataset credits and their licenses apply to both. No upstream asset is relicensed by the project MIT license.
