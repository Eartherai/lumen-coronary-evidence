# Publish Lumen from the verified release

The 11 October work is a local source upgrade. The human will publish GitHub, upload YouTube and submit Devpost. No account login, repository creation, push, hosting deployment or submission has been performed by preparing this handoff.

At the publication check, this checkout had no Git remote and GitHub CLI had no authenticated host. The current verified baseline is the 10 October complete-cohort package, not the historical ZIP under `dist`. The final 11 October upgrade needs its own source package and exact verification result before the publication commands below are used.

## Release to use

| Item | Verified 10 October baseline |
|---|---|
| Source | `output/submission-2026-10-10-audit/lumen-source.zip` |
| Source SHA-256 | `1137b487c87fc4397d8af3bce7912f44c3f41c7aff854e3147f9ce346334dff2` |
| Size / payload | 55,376,902 bytes / 216 manifest files |
| Exact source receipt | `output/submission-2026-10-10-audit/source-verification.json` |
| Matching commit | `279f46c26b154c8d850dc8e3fd800866f5978a2f` |
| Outer review ZIP | `output/lumen-track-a-review-package-2026-10-10.zip` |
| Outer ZIP SHA-256 | `7a04a9d538bc69163732144a8d17306afd9f9d4158c8a33b488e540aea85e044` |

Every tracked application/document/media file matched that source package at this audit. The two omitted tracked files are video-editor `.media` ledger files, which are deliberately excluded from the packaged source. The source manifest and embedded verification digest match the passed clean-extraction record. The 61-record final holdout was not rescored.

The original `dist/lumen-submission-source.zip`, SHA-256 `9dc17d5ea64e0eb3f5c84eb1811d7612e2a578fa8e951d2d8074065d21953cdc`, is a preserved historical release. Its own verification describes that older payload. Use the new 11 October source archive and receipt supplied by the root release review for the upgraded app; record their path, hash and final source commit in `publication-fields.json`.

The current verified video is `output/video/lumen-demo.mp4`: **5:42.83**, 1920×1080, 24 fps, H.264/AAC, English synthetic Kokoro narration. Its SHA-256 is `50ac052afe6f583e79d6deb02b6c40fcfb4dd106e499b1a10dbdb6173cabe53e`. The six-page report is `output/pdf/lumen-report.pdf`. The older dated `final-kit-2026-10-10` copy describes a previous 4:40 video; use the current `submission/devpost-draft.md`, current report/video and this handoff.

## Public repository contents

Publish the final reviewed Git commit from this repository. The required source/data/evidence are already represented by this structure:

```text
.github/workflows/pages.yml
README.md  REPRODUCIBILITY.md  LICENSE  THIRD_PARTY_NOTICES.md
package.json  package-lock.json  requirements-training.txt
server.py  inference.py
public/                  interface, anatomy, compact SHAP certificates
artifacts/               portable models, cohort audit and evaluation evidence
scripts/                 static build, exporters and release verification
tests/                   Python and browser parity/route checks
training/                source workbook, fixed split, training code and receipts
docs/cohort-audit.md
submission/              freeze, clinical groups, disclosure and current draft
output/pdf/              six-page report and report review evidence
output/video/            verified video and its QA
output/cohort-browser-review/
```

Keep the full-cohort SHAP receipt at its existing path: `training/cohort-audit-verification/shap-20261009T200701.871364Z/verification.json`. The compact certificate includes that path and exact hash. All ten source bindings and the full receipt are tracked; the static builder rejects missing or changed bound files. Neither renaming that receipt directory nor removing training evidence is needed to publish.

At the audit, Git held 218 tracked files totaling 78,161,436 bytes. Its largest tracked file was the 25,469,444-byte demonstration MP4, below GitHub's enforced 100 MB object limit. The existing tracked tree can be pushed normally. Keep distributable ZIP packages and future media builds outside the Git tree and upload them as release assets if desired. A later media-only release can reduce clone size, but it would require updating README links and verifying the revised source tree; it is unnecessary for the current publication. [GitHub repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits).

The read-only Git signature check found no matches in the 218 tracked working files, 349 raw Git metadata files and 268 stored blob/commit/tag objects. `git-secret-scan.json` records counts and filenames only. The check uses explicit secret signatures; it does not expose matched content or account identity.

## Human GitHub commands

Run these after the final 11 October source changes have been reviewed, committed and verified locally. The repository slug is a proposed name; change only `lumen_repo` if another name is preferred. Account owner and returned URLs are read from the human's actual authenticated account.

```sh
cd '/Users/earther/Desktop/IIT mandi/coronary-evidence'
git status --short --untracked-files=no
git diff --quiet
git diff --cached --quiet
gh auth login --hostname github.com --web --git-protocol https
gh auth setup-git
lumen_owner=$(gh api user --jq .login)
lumen_repo='lumen-coronary-evidence'
lumen_repository="$lumen_owner/$lumen_repo"
gh repo create "$lumen_repository" --public --source=. --remote=origin
git push --set-upstream origin HEAD:main
gh repo edit "$lumen_repository" --default-branch main
gh repo view "$lumen_repository" --json url,visibility,defaultBranchRef
git rev-parse HEAD
```

Run each command successfully before proceeding to the next. A tracked dirty status means the final source commit is still being prepared. Untracked dated review packages are not automatically staged by these commands. [GitHub CLI repository creation](https://cli.github.com/manual/gh_repo_create).

Open the returned repository URL in a signed-out browser. Check README rendering, report download, the disclosed assistance, and the source files. Test `npm ci` and `python3 server.py` from a fresh clone. Save the actual repository URL, final commit and report link in `publication-fields.json`; no public URL is inferred from the proposed slug.

## Optional free Pages demo

The included Pages workflow installs Node 24/Python 3.12, uses the pinned Three.js lockfile, runs Python and JavaScript checks, builds `dist/site`, tests inference and repository subpaths, then uploads precisely `dist/site`. Its paths are relative to the repository root; the published entry is the site's `index.html`. The workflow deploys after a push to remote `main` or manual dispatch.

After creating the repository, set **Settings → Pages → Build and deployment → Source: GitHub Actions**. The equivalent command for this newly created repository is:

```sh
gh api "repos/$lumen_repository/pages" --method POST -f build_type=workflow
gh workflow run pages.yml --repo "$lumen_repository" --ref main
gh run list --repo "$lumen_repository" --workflow pages.yml --limit 3
```

Open the returned workflow run and wait for a successful deploy. Obtain the actual returned site URL:

```sh
gh api "repos/$lumen_repository/pages" --jq .html_url
```

The POST command configures a new Pages site; if the site was already configured through Settings, omit that POST and dispatch the workflow. GitHub documents `build_type=workflow` for Actions publishing. [Pages API](https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site), [workflow dispatch](https://cli.github.com/manual/gh_workflow_run).

Open the returned URL while signed out. Verify the mesh loads, the complete cohort filters work, one profile cell synchronizes the case, edited inputs recompute, recorded outcomes reveal, unlabelled inputs work, and provenance/evidence links open. Save only that verified URL. The static app needs no Python model service or paid API. Public development examples and recorded labels are downloaded; entered form values remain in browser memory. Hosting is optional; required source and video links still need their separate visibility checks.

## YouTube and Devpost

Upload the verified MP4 to the human's actual channel with **public or unlisted** visibility. The supplied submission guideline requires 3–10 minutes, a running-system demonstration and English audio or subtitles. Use this title:

**Lumen — Coronary Evidence Explorer | Multimodal AI Hackathon 2026 Track A**

Use this description after replacing the actual link fields:

> Lumen makes coronary predictions inspectable across a public development cohort: compare five independently fitted input profiles, select source-identified reference anatomy, trace grouped linear SHAP explanations, and reveal recorded mistakes. Educational research only; not clinically validated or patient-specific lesion mapping. OpenAI Codex assisted with research, software, experiments and presentation. English narration was generated locally with Kokoro. Source: [actual public GitHub URL]. Six-page report: [actual public report URL]. Optional interactive demo: [actual verified URL, if published].

Check playback while signed out, including audible English narration, and save the actual watch URL. Paste the current `submission/devpost-draft.md` into the actual Devpost project. Add real full names and Devpost accounts for every actual teammate; select Track A. List OpenAI Codex and Kokoro in **Built With**, along with the actual stack. Save the actual submission confirmation and project URL after Devpost confirms receipt.

The supplied guideline's four required components are project description, public GitHub with setup/run README, public/unlisted YouTube, and actual human team members with Devpost accounts. Track A limits the technical report to six pages. The 11 October live rules retain 1–4 team members, one track per team and membership in one submitting team per person. The displayed deadline is **15 October 2026 at 00:15 IST**. The overview labels participation “Students only” while rules prose says primarily college students; real eligibility must reflect the human's status and actual event declarations. [Official overview](https://multimodal-ai-hackathon-2026-7.devpost.com/), [official rules](https://multimodal-ai-hackathon-2026-7.devpost.com/rules).

## Independent source CI

The existing source checks run as part of optional Pages publishing. `source-ci.yml` in this folder is a prepared independent source gate for push, pull request and manual dispatch, using the same pinned actions and existing meaningful checks. The root installed it at `.github/workflows/source-ci.yml`, including outcome-direction and runtime-lifecycle checks, without requiring Pages to be enabled. It verifies the exact saved SHAP certificate/source bindings through the static builder; it does not fit models or rescore the final holdout.

The root release review owns the final browser/performance checks and the newly verified 11 October package. This folder supplies publication commands and unresolved factual fields; it is not a substitute for that changed-source release receipt.
