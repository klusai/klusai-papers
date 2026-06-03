# klusai-papers

arXiv-style papers for the KlusAI Privacy program. Results are auto-ingested from the
`klusai-models` / `europriv-bench` repos (the `post_training_pipeline.sh` pattern from
`diacritics-finetuning-code`) so paper numbers trace back to a commit.

## Planned papers

| # | Dir | Title | Status |
|---|-----|-------|--------|
| 1 | `papers/europriv-bench/` | **EuroPriv-Bench: A Unified Pan-European De-identification Benchmark with Privacy-Utility Metrics** | flagship — ships first |
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
make europriv-bench      # build one paper's PDF (requires latexmk + a TeX distribution)
```

`make results` makes the paper build reproducible (it doesn't depend on a developer having
run the pipeline by hand). The ingested JSON should be validated against `europriv_bench`'s
versioned results schema before `\input` so paper numbers trace to a known harness +
taxonomy version.

## Reproducibility & submissions

Papers and the public EuroPriv-Bench leaderboard share one reproducibility bar:

- [`SUBMISSIONS.md`](SUBMISSIONS.md) — public submission protocol for adding a model to the
  leaderboard (HF model id + adapter scheme + model card; scored by CI, never self-reported).
- [`ARTIFACT_EVALUATION.md`](ARTIFACT_EVALUATION.md) — per-track artifact-evaluation program
  (ARR Responsible NLP + ACL reproducibility for NLP papers; ACM Artifact Evaluation
  Available+Functional for the PETS/PoPETs path) and the shared pass criterion.
