# Paper 1 publication packaging

## Local build

Requirements: Python 3.13, Docker, and `python3.13 -m pip install -r requirements-check.txt`.
Run `make check && make arxiv`. Outputs are `dist/paper1.pdf` and
`dist/paper1-arxiv.tar.gz`; the final TeX log is `build/paper1/verified.log`.
No training, inference, results download, or paid service is invoked.

The previous repository Makefile used host `latexmk`; it had no committed Docker
configuration. Paper 1 now uses the locally available `texlive/texlive` TeX Live 2026 image,
pinned by its multi-architecture digest in `Makefile`, both locally and in CI. Other
paper targets retain their existing host toolchain. `TEX_IMAGE=... make arxiv` overrides
the image without editing the build. Build files travel through Docker's input/output
streams, so a shared daemon does not need access to a host filesystem mount.

The builder stages fresh sources, rewrites the shared bibliography to a local relative
path, runs pdfLaTeX/BibTeX via latexmk, and gathers referenced figures/styles using the
TeX recorder. The archive includes `main.tex`, `main.bbl`, `klusai.bib`, and any referenced
local assets, with relative member paths and stable archive headers. It excludes the
compiled manuscript PDF and temporary build files. Literal absolute/parent input paths
are rejected. The current paper has no external figures.

The archive is then extracted into a separate directory, transferred alone, and rebuilt
with two pdfLaTeX passes, without BibTeX, network access, or shell escape. Missing inputs,
undefined citations/references, missing glyphs, and overfull boxes fail the build. The
distributed PDF comes from that isolated rebuild. This follows the
[arXiv TeX source guidance](https://info.arxiv.org/help/submit_tex.html); arXiv's own
server processing and acceptance still require an identity-bound submission.

## Title reconciliation (2026-10-11)

Canonical title: **EuroPriv-Bench: A Unified Pan-European De-identification Benchmark
with Re-identification Risk Metrics**.

| Surface | Finding / action |
| --- | --- |
| Website `_papers/europriv-bench.md` on `klusai.github.io/main` | Uses the canonical title; read-only reference. |
| Paper TeX, both CFF titles, README, shared BibTeX | Previously ended in “Privacy-Utility Metrics”; aligned to the website. |
| HF `klusai/europriv-bench` card | Heading is “EuroPriv-Bench (v0 — detection)”; no full paper title or citation found. Left unchanged. |
| `.zenodo.json` and release notes | Use the canonical title. |

Sources: [website source](https://github.com/klusai/klusai.github.io/blob/main/_papers/europriv-bench.md),
[research page](https://research.klusai.com/papers/europriv-bench/), and
[HF card](https://huggingface.co/datasets/klusai/europriv-bench/blob/main/README.md).
The website names “KlusAI Research”; the TeX/CFF name “KlusAI”. Zenodo preserves the
repository's existing collective author, without inventing individual identities/ORCIDs.
The HF card still refers to a native-speaker review/IAA gate. RES-77's assigned protocol
instead uses an LLM panel; this repo's limitations say so explicitly, and do not assert
that any config has passed. These external discrepancies are reported, not edited.

## Release and DOI

`.github/workflows/paper1-release.yml` runs only on pushed `paper1-v*` tags. It runs checks,
builds the PDF and archive, creates/resumes a draft GitHub Release, uploads both assets,
then publishes the release. It refuses to overwrite an already published release.
Tags must already exist remotely (`--verify-tag`); the workflow cannot create a tag.
No tag, push, release, or public upload is part of local `make` commands.

Zenodo's GitHub integration must already be enabled for this repository by the account
owner. That account linking is identity-bound; the workflow needs only `GITHUB_TOKEN`,
not a Zenodo API token. Once enabled, release publication triggers DOI archiving.
`.zenodo.json` describes an Apache-2.0 preprint, collective author, keywords, and links
to GitHub, the dataset, and the research page. Zenodo
[prefers this file over CITATION.cff](https://help.zenodo.org/docs/github/describe-software/).
No placeholder DOI is fabricated. Account linking, actual DOI minting, hosted Actions
execution, and arXiv upload have not been verified by this local task.

## Manuscript scope

The publication toolchain is separate from scientific completeness. The existing Paper 1
TeX still has unfilled taxonomy, benchmark-construction, metrics, and baseline sections;
the abstract's baseline-study statement is not backed by a results table in this source.
The website contains a more developed manuscript. Transcribing its numbers without
checking the harness evidence would violate the claims discipline and is outside this
packaging change. No benchmark numbers or claimed wins are added. Scientific submission
readiness remains open until those sections and harness-backed evidence are reconciled.
