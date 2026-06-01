# Artifact-Evaluation Plan

This document defines the **per-track artifact-evaluation program** for the papers in this
repo. It complements the public leaderboard [submission protocol](SUBMISSIONS.md): both share
**one reproducibility bar** — a pinned harness/taxonomy/dataset triple, a Zenodo DOI, and a
one-command reproduction.

## Per-track program

Different papers in this repo target different venues, which run different artifact tracks. We
commit to the program that matches each track:

| Paper track | Venue family | Artifact program |
|-------------|--------------|------------------|
| NLP papers | ARR / ACL venues | **ARR Responsible NLP checklist** + the **ACL reproducibility track** |
| Privacy papers | PETS / PoPETs | **ACM Artifact Evaluation** — **Available** + **Functional** badges |

- **ARR Responsible NLP checklist + ACL reproducibility track.** NLP submissions go through
  ARR and complete the Responsible NLP checklist (data, compute, limitations, risks) and the
  reproducibility checklist; the artifact is released and pinned so the reported numbers can be
  regenerated.
- **ACM Artifact Evaluation (Available + Functional).** The PETS/PoPETs path follows ACM's
  Artifact Review and Badging. We target the **Available** badge (artifact publicly archived
  with a DOI) and the **Functional** badge (artifact is documented, consistent, complete, and
  exercisable). We do not claim **Reproduced**/**Reusable** badges unless a track explicitly
  evaluates and awards them.

## Pass criterion

An artifact **passes** when it provides, together:

1. a **Zenodo DOI** archiving the released artifact (→ Available);
2. a **pinned harness/taxonomy/dataset triple** — the same provenance triple stamped on every
   leaderboard row (see [`SUBMISSIONS.md`](SUBMISSIONS.md)); and
3. a **one-command reproduction** that regenerates the paper's reported numbers from that
   pinned triple (→ Functional).

> **Zenodo DOI + pinned harness/taxonomy/dataset triple + one-command reproduction = Available + Functional.**

This is the bar for both the ACM-AE Available+Functional path and the ARR/ACL reproducibility
track; the deliverable is the same, only the badge/checklist wording differs by venue.

## Venue hygiene

- **arXiv-first is ARR-compatible.** Posting a preprint to arXiv before/while under ARR review
  is allowed; we default to arXiv-first.
- **No double submission.** No paper is under review at two venues at the same time. A paper
  moves to a second venue only after it is withdrawn from or rejected by the first.

## Relationship to the leaderboard

The artifact's pinned triple is the **same triple** the leaderboard submission CI stamps onto
each row (KLU-16, specified in [`SUBMISSIONS.md`](SUBMISSIONS.md)). `make results` ingests the
committed `leaderboard.json`, so a paper's artifact and its leaderboard row reference identical
provenance and clear the same reproducibility bar.
