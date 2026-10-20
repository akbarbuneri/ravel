# RAVEL: Risk-Aware, Validated Evolution of LLM Harnesses

Research code, data and paper for **"Accuracy Is Not Acceptance: Risk-Aware, Budget-Constrained
Selection of LLM Harness Revisions"**, a follow-up study to *Harness Learning Enables Generalizable
Test-Time Adaptation* (Zhang et al., arXiv:2609.35738).

- Paper: `paper/main.pdf` (source in `paper/main.tex`, `paper/sections/`, tables and figures in `paper/generated/`)
- Status: v1.0. The main study is complete: 9 units × 4 rounds × K=4 proposals × 3 policies, with real LLMs.

## What is here

| Path | Contents |
|---|---|
| `ravel/env/finsynth.py` | FinSynth: synthetic companies, corpus, tools, six task families, splits, grader |
| `ravel/sandbox.py`, `ravel/sandbox_child.py` | Network-isolated (`unshare -rn`) harness execution with a capability broker that meters tokens, models latency, injects faults and logs violations |
| `ravel/static_check.py` | Static policy rules (imports, banned names, entitlement invariant, answer leakage, size cap) |
| `ravel/proposer.py` | Proposer prompts, execution reports, handler-revision composition, adversarial mutations |
| `ravel/policies.py` | Accuracy-only, hard-gate and RAVEL acceptance policies, plus ablations |
| `ravel/llm.py` | Ollama client with a deterministic persistent cache |
| `ravel/core.py` | v0.1 acceptance prototype (Wilson bound), kept for continuity |
| `harnesses/seed.py` | Seed harness |
| `experiments/run_study.py` | Main study driver (lockstep rounds, common random numbers, resumable) |
| `experiments/analyze.py`, `experiments/report.py` | Ground-truth analysis, decision-level gate analysis, sweeps, tables and figures |
| `experiments/proposer_capability.py` | Proposer capability probe summary (paper appendix) |
| `results/study/` | Every candidate program, evaluation episode and decision of the main study, plus `analysis.json` |
| `results/llm_cache.sqlite` | Every LLM response. Re-running replays it exactly |
| `results/proposer_probe_*` | Proposer capability probes |
| `results/pilot/` | Early debugging pilot (superseded settings: wall-clock latency, 4B rewrite proposer). Not used in the paper |

## Reproduce

Requirements: Linux with `unshare` (user namespaces), Python ≥ 3.10, numpy, scipy, matplotlib, requests,
and Ollama serving `qwen3.5:4b` (solver) and a Qwen3.5-9B model (proposer, tag `qwen35-faster:latest`
in our setup).

```bash
python -m venv .venv --system-site-packages && .venv/bin/pip install matplotlib
.venv/bin/python -m unittest discover -s tests -v       # 19 tests
.venv/bin/python -m experiments.run_study                # replays from cache in seconds; a fresh run takes ~6.5 h on one RTX 3070
.venv/bin/python -m experiments.analyze --study results/study
.venv/bin/python -m experiments.report  --study results/study --out paper/generated
cd paper && tectonic main.tex
```

## Headline results (see the paper for CIs and caveats)

- Accuracy-only gates passed 8 of 35 held-out-harmful candidates, including an entitlement bypass that also raised accuracy. Under an adversarial proposer, an answer-leak edit captured the incumbent and froze adaptation (+0.5 pp vs +6.0 pp clean).
- RAVEL passed 2 of 35 harmful candidates, never accepted a mutated edit, and beat point-estimate hard gates by +4.3 pp (95% CI [0.5, 8.8]). It was **not** reliably better than accuracy-only (+1.2 pp, CI [−5.9, 7.7]).
- RAVEL's cost: it rejected 13 of 20 beneficial candidates, 9 of them through an uncalibrated 20k-character size cap (post-hoc analysis: without the cap it passes 16 of 20).
- No policy fixed the seed's prompt-injection vulnerability, which was absent from the objective. Stacked revisions bloated harnesses until proposal validity dropped to 25%.

## Security note
The sandbox is a research isolation layer: no network namespace, rlimits, restricted builtins and an import allow-list. It is not a hardened production sandbox. The security gates are measured test-suite constraints, not proofs.
