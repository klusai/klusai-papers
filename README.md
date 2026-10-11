# klusai-papers

arXiv-style papers for the KlusAI Privacy program. Results are auto-ingested from the
`klusai-models` / `europriv-bench` repos (the `post_training_pipeline.sh` pattern from
`diacritics-finetuning-code`) so paper numbers trace back to a commit.

## Planned papers

| # | Dir | Title | Status |
|---|-----|-------|--------|
| 1 | `papers/europriv-bench/` | **EuroPriv-Bench: A Unified Pan-European De-identification Benchmark with Re-identification Risk Metrics** | flagship — ships first |
| 2 | `papers/synthetic-drift/` | Closing the synthetic-to-real gap in multilingual legal/clinical PII generation | dataset paper |
| 3 | `papers/underserved-sota/` | Open SOTA de-identification for under-served European languages | model paper |
| 4 | `papers/privacy-utility/` | Privacy-utility & re-identification-risk tradeoffs in anonymization | eval paper |
| 3* | `papers/dissociation-protector/` | **Detection Is Not Re-identification: A Unified Dissociation and an Open Protector** | KLU-110 — skeleton draft (gated on KLU-27 validation; not for submission) |

Positioning discipline (from the external prior-art review): claim **"first *unified*"**, not
"first"; cite and subsume TAB / AI4Privacy / MAPA / MultiGraSCCo; frame synthetic generation
as infrastructure and the taxonomy as standardization.

## Layout

```
shared/klusai.bib   shared bibliography (prior art + KlusAI artifacts)
papers/<slug>/       main.tex + paper-specific refs.bib
results/             JSON/markdown results ingested from other repos (gitignored build inputs)
```

## Build

```bash
make results             # pull europriv-bench's committed leaderboard.json into results/ (reproducible)
make install check       # Python 3.13; install shared dev tools and run all offline checks
make arxiv               # Paper 1 PDF + verified source tarball (requires Docker)
make europriv-bench      # same Paper 1 build; other paper targets use local latexmk
```

Paper 1 artifacts are `dist/paper1.pdf` and `dist/paper1-arxiv.tar.gz`.
The Docker TeX image is pinned in `Makefile`; `TEX_IMAGE` can override it for compatibility checks.
See [`docs/PAPER1_PUBLICATION.md`](docs/PAPER1_PUBLICATION.md) for the build contract,
title reconciliation, release automation, and remaining manuscript limitations.

`make results` makes the paper build reproducible (it doesn't depend on a developer having
run the pipeline by hand). The ingested JSON should be validated against `europriv_bench`'s
versioned results schema before `\input` so paper numbers trace to a known harness +
taxonomy version.

## Local checks and PR CI

Use Python 3.13 in a virtual environment, with `bash` and `jq` on PATH:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
make install
make check
```

The `test` CI job runs the same Ruff lint/format checks and offline unit tests on PRs
and pushes to `main`. Tests check paper environments, references, citations and figures,
plus auto-merge behavior using a fake GitHub CLI. They do not compile PDFs, download
HF assets, ingest sibling-repo results, or validate benchmark numbers. Publication packaging and metadata checks run in the same suite; no existing tests are skipped.

Auto-merge is ported from [rb-cli](https://github.com/klusai/rb-cli/blob/main/.github/workflows/auto-merge.yml).
It squash-merges eligible PRs through GitHub native auto-merge. Before enabling it, an
admin must allow repository auto-merge and protect `main` with the required `test` check.
The workflow stays inactive if it cannot verify that protection via GitHub's branch API;
ruleset-only protection that does not expose the required check there also stays inactive.
Configure Codex review separately in the repository's review settings; this workflow
does not request reviews or replace any required review rules.

Drafts and `needs-review`/`hold` labels are hard stops and disable queued auto-merge.
Forks, `review/` or `hold/` branches, and Dependabot major/unknown updates need the
maintainer's `automerge` label; that label never overrides a hard stop. The privileged
workflow reads current PR metadata and never checks out PR code. It does not update
stale branches, so requiring up-to-date branches can leave auto-merge waiting.

## Reproducibility & submissions

Papers and the public EuroPriv-Bench leaderboard share one reproducibility bar:

- [`SUBMISSIONS.md`](SUBMISSIONS.md) — public submission protocol for adding a model to the
  leaderboard (HF model id + adapter scheme + model card; scored by CI, never self-reported).
- [`ARTIFACT_EVALUATION.md`](ARTIFACT_EVALUATION.md) — per-track artifact-evaluation program
  (ARR Responsible NLP + ACL reproducibility for NLP papers; ACM Artifact Evaluation
  Available+Functional for the PETS/PoPETs path) and the shared pass criterion.
