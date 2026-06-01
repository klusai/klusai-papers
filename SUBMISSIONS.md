# Submission Protocol

This document defines the **public submission protocol** for the EuroPriv-Bench leaderboard.
It exists so that papers in this repo and the public leaderboard share **one reproducibility
bar**: a number on the leaderboard and a number in a paper trace back to the same pinned
harness, taxonomy, and dataset.

For the per-track **artifact-evaluation** program (ARR / ACL / ACM-AE), see
[`ARTIFACT_EVALUATION.md`](ARTIFACT_EVALUATION.md).

## Scope

There are two ways results enter the program, with different processes but the same bar:

| Path | Who | Where | Process |
|------|-----|-------|---------|
| **Leaderboard submission** | any third party | `europriv-bench` repo | open a PR (below) |
| **Paper artifact** | KlusAI papers in this repo | venue artifact track | [`ARTIFACT_EVALUATION.md`](ARTIFACT_EVALUATION.md) |

The submission **CI** that builds and scores third-party entries lives in `europriv-bench`
(tracked in **KLU-16**). This document specifies the *contract* a submitter must satisfy; it
does **not** re-implement that CI here.

## How to add a model to the leaderboard

A third party adds a model by opening a pull request against `europriv-bench`. The PR must
contain, and only contain:

1. **A Hugging Face model id** — a public, versioned reference (pin a revision/commit, not a
   moving tag), e.g. `org/model@<sha>`.
2. **An adapter scheme** — which built-in adapter the harness uses to call the model
   (e.g. token-classification, generative-extraction, or Presidio-style pipeline) plus any
   declared config. No arbitrary submitter code is executed beyond the declared adapter.
3. **A filled model card** — the template in `europriv-bench` (training data provenance and
   licensing, intended use, languages/domains covered, known limitations, contamination
   statement against the held-out gold split).

The submitter does **not** submit scores. Scores are produced by CI, never self-reported.

## What CI does (contract)

When the PR is opened, the `europriv-bench` submission CI (KLU-16):

1. **Builds the adapter** from the declared scheme + the pinned HF model id.
2. **Runs `europriv run`** on the **public** benchmark configs, inside a **no-secrets
   sandbox** — no network egress to submitter-controlled endpoints, no access to repository
   secrets, no access to any held-out material beyond what the public configs expose. This
   keeps an external PR from exfiltrating secrets or gaming the gold split.
3. **Validates the model card** against the schema (required fields present; contamination
   statement present).
4. **Appends a provenance-stamped row** to `baselines/leaderboard.json`: the score plus the
   harness version, taxonomy version, dataset version, the pinned model revision, and the CI
   run id. Every row is reproducible from the triple it stamps.

A submission that fails the build, the run, or card validation does not get a row.

## Provenance contract

Every leaderboard row is stamped with the **pinned triple**:

- **harness** version (the `europriv` runner / `europriv_bench` package),
- **taxonomy** version (the harmonized KP taxonomy),
- **dataset** version (benchmark split + revision),

plus the model revision and CI run id. This is the same triple the artifact-evaluation pass
criterion pins (see [`ARTIFACT_EVALUATION.md`](ARTIFACT_EVALUATION.md)), so a leaderboard row
and a paper table cite the same provenance.

`make results` in this repo ingests `europriv-bench`'s committed `leaderboard.json`, so paper
numbers inherit this provenance directly.
