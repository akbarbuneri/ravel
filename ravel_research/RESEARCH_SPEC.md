# RAVEL — Research Specification v0.1
Date: 2026-10-19
Status: v0.1 preregistration (19 Oct 2026). Executed as v1.0 on 19–20 Oct 2026 with these deviations, all reported in the paper: Qwen3.5-9B handler-mode proposer (the 4B proposer produced no improvements in a capability probe); 3 conditions × 3 seeds × 4 rounds × K=4 because of single-GPU compute; one financial environment (FinSynth); latency modeled from tokens. Results: paper/main.pdf.

## Research statement
Investigate whether uncertainty-aware, budget-constrained and regression-preserving selection of LLM harness edits produces better operating-point tradeoffs than accuracy-only selection, under matched total optimization budgets and independently held-out environments.

## Independent variables
Selection policy: accuracy-only, deterministic hard constraints, Wilson-confidence gates, uncertainty-aware multiobjective constrained selection, RAVEL with fault diagnosis.
Feedback quality: perfect labels; 5%, 10%, 20% mislabeled; stale data; intermittent tool errors.
Budget: identical candidate proposals, solver calls, feedback labels, and logged tokens; report aggregate wall-time and energy only where measured.
Task shift: held-out templates, new data generators, alternate language phrasing, changed tool schemas, unseen solver models.

## Outcomes (report ALL)
Primary: task success, protected-task regression rate, violation rate on adversarial cases, total search tokens, p95 latency, accepted-edit rate. Secondary: Brier score of safety/risk predictions where probabilistic, abstention rate, Pareto hypervolume, edit complexity, post-selection evaluation score. No single composite metric conceals constraint violations.

## Research environments
A: Synthetic financial-query benchmark with fixtures and answer calculators: arithmetic, restatements, period alignment, provenance, bilingual paraphrase.

B: Untrusted tool-output and capability benchmark with adversarial response strings, static policy checks, and runtime network/filesystem isolation.

C: State-dependent multi-workflow benchmark for multi-round regression and retention tests.

D: Fault-injection benchmark with timeouts, schema drift, label noise, stale source values, and ambiguous root cause.

## Dataset plan
At least 5 task families; pilot 50 adaptation and 50 validation questions per family; full study minimum 200 adaptation, 200 validation, 500 strictly hidden test cases per family (subject to power analysis). Organize by generator/template, not random question only. Final counts determined by preregistered power analysis; task families never shared across cross-family-transfer evaluation. Maintain separate protected regression sets and adversarial sets; do not expose hidden test outcomes to proposer or selection logic. Fix seeds and publish generators.

## Baselines
B0 seed immutable; B1 repeated solver calls + best of N under same budget; B2 LLM code editor with no feedback; B3 accuracy-only propose/test/select; B4 fixed hand-built constraints without diagnosis or uncertainty; B5 RAVEL. Add original trained proposer if source and checkpoints are verifiable; label any reconstruction as approximate. Compare against HarnessEvolve where accessible and compatible, without suggesting its published numbers are directly comparable.

## Experimental methodology
1. Freeze generator code, benchmark specs, data partitions, prompts and budgets before confirmatory run.
2. For each baseline, expose identical adaptation observations and cap total proposal/solver/token/evaluation budgets. Publish best-effort budget matching and all deviations.
3. Develop on adaptation set; use validation data for revisions/selection; touch final test once per preregistered run.
4. At least 5 random seeds for pilot, 10 for confirmatory if feasible; task-stratified paired bootstrap 95% confidence intervals; Holm-corrected multiple comparisons and report raw results.
5. Track rejected edits and the reason; include static check false-positive/false-negative rates against labeled adversarial examples. Explicitly report missed violations and the test coverage limitation.
6. Conduct ablations: no fault classifier, no regression gate, no confidence gate, no cost gate, no security gate, no diagnostic feedback. Use exactly the same proposer and test material when possible.
7. Report full Pareto frontier and fixed-budget success; record no-change as a valid decision; repeat with alternate models.

## Algorithm proposal
For current harness h and feedback D: estimate fault causes; if evidence points to upstream non-harness failure, abstain or route incident to data/tool handling. Otherwise generate K patch candidates, apply to isolated snapshots, run syntax/policy/sandbox tests; evaluate on independent scoring and protected cases. Estimate upper confidence bound of protected regression and upper cost/latency. Reject candidates whose upper bounds violate preregistered limits; rank survivors by quality improvement minus normalized cost penalties; abstain if none qualifies. Keep immutable audit trail and rollback snapshot. Avoid using final hidden test in candidate selection.

## Threats to validity
Hard constraints are only measured test-suite constraints, not proofs of safety. Wilson intervals assume independent Bernoulli-like cases; correlated examples call for cluster bootstrap or hierarchical uncertainty estimates. Runtime p95 needs sufficient sample size and repeatable load. Synthetic financial QA can advantage deterministic calculators. Generated adversarial examples may not represent realistic attackers. Selection consumes development labels and can overfit even with held-out final testing. Fine-tuning a proposer is separate from this initial selection-policy study.

## Success criteria for a confirmatory finding
Under equal total optimization budgets, demonstrate statistically supported reduction in protected regressions and/or adversarial violations at noninferior task accuracy and within prespecified latency/cost constraints, in at least two distinct held-out environments. If no improvement, report the negative finding with confidence intervals and compute costs. Do not claim general security or autonomous production readiness.

## First two-week sprint
D1 pin versions, select models, freeze task generators and licenses; D2 build typed harness/tool protocol, trace schema and deterministic oracle; D3 isolate untrusted execution via external container/sandbox with network off and resource quotas; D4 build 4 baseline strategies; D5 implement full run ledger; D6 build synthetic test families; D7 run 50-case sanity pilot; D8 debug label leakage and fairness; D9 run pre-registered small baseline experiment; D10 freeze benchmark split and publish pilot methods, logs, cost summary and blocker list. Milestone: one end-to-end scored candidate with reproducible accept/reject decision and immutable trace; no real-world security claims.

## Publication requirements
Code, licenses, synthetic data generation, environment manifest, stable run IDs, seed list, raw predictions and answers, code patches, evaluation traces, candidate selection logs, model checkpoints or access instructions, test statistical scripts, compute/cost tables, and instructions to reproduce all figures.
