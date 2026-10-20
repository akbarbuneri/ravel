# RAVEL research plan: complete, compare, then decide

Date: 2026-10-20

Status: revised after identifying close prior work and reviewing rounds 1–2. The immediate priority is to finish and assess the existing study. Scoped acceptance is a deferred hypothesis, not an approved next implementation step or a demonstrated novel method. Preserve the current study protocol.

## Immediate recommendation and investment boundary

Finish the planned rounds, freeze the artifacts, and perform a bounded analysis and literature comparison before starting a larger project. Current results justify completing the study; they do not yet justify building the full extension below.

The strongest candidate contribution is an empirical study of the tradeoff between regression prevention and useful adaptation, isolating acceptance policies where possible. Do not position gated harness self-improvement itself as new. A new combination of existing gates is insufficient on its own to establish a strong methodological contribution.

After the final analysis, choose among a focused empirical paper, a replication/technical report, or a small separately preregistered extension. Do not add complexity merely to obtain a novelty claim or tune the method against the already inspected held-out outcomes.

## Closest prior work to compare before expansion

These are publicly available preprints; arXiv availability alone does not establish peer-reviewed acceptance. The overlap summaries below are an initial literature screen, not a completed full-method comparison.

| Work | Relevant overlap | Required comparison |
| --- | --- | --- |
| [Self-Harness](https://arxiv.org/abs/2606.09498), June 2026 | Minimal harness revisions followed by regression testing | Acceptance rule, protected evidence, and regression/adaptation tradeoffs |
| [HarnessFix](https://arxiv.org/abs/2606.06324), June 2026 | Trace-grounded diagnosis, scoped repair operators, regression-aware validation | Distinguish scoped repair generation from independently evaluated deployment routing; compare diagnosis mechanisms |
| [RRSI](https://arxiv.org/abs/2609.24972), September 2026 | Proposal and selection regularization addressing memorization, noisy gains, and cost | Highest-priority comparison: selector, leakage screening, noise handling, cost controls, and ablations |
| [RegenHarness](https://arxiv.org/abs/2609.27612), September 2026 | Evidence-gated changes, regression checks, release authorization, rollback in robotics | Separate domain and implementation differences from actual methodological differences |

Read the full algorithms and experimental protocols, then build a claim-by-claim comparison. If feasible and compatible, include a faithful acceptance-policy baseline inspired by the closest method in a separately specified follow-up. Clearly label any reconstruction and account for changed proposal distributions and budgets. Do not imply that the current hard-gates baseline represents these methods or that published scores are directly comparable.

## Current-study questions and decision point

Use the completed study to answer:

1. How often does each policy accept revisions that deteriorate on held-out tasks, and how much deterioration occurs?
2. How many useful gains does conservative acceptance reject, including small gains below the existing three-answer “beneficial” threshold?
3. Which components change decisions beyond hard gates, and are those differences practically meaningful?
4. How much of the observed behavior comes from proposer reliability, benchmark construction, shared candidates, or deliberately injected mutations?
5. What finding remains distinct after comparison with the closest prior work?

Report continuous held-out gains and losses as well as predefined categorical metrics. Do not redefine outcome thresholds after inspecting results. Account for shared parents, candidates, tasks, and conditions in uncertainty estimates; repeated appearances of one candidate are not independent confirmations. Audit actual proposal, solver, token, and evaluation budgets rather than assuming identical proposal counts imply identical total compute once trajectories diverge.

Proceed with a focused empirical paper if the completed evidence supports a precise, informative finding beyond the closest work. If findings mainly reproduce existing conclusions, prefer a modest replication or technical report. Consider the scoped extension only if a specific unresolved problem and a plausible advantage over simple routing remain after that review.

## Motivation

Current RAVEL evaluates candidate harness revisions through validity, security, cost, regression, improvement, and fault-awareness gates. Its main decision is whether to accept a revision into the incumbent harness.

The completed first main-study round provides a reason to investigate a more local decision:

- Two revisions in the noisy condition improved held-out accuracy from 42/72 (58.3%) to 50/72 (69.4%) and 49/72 (68.1%). The gains were on Arabic questions, with no losses among previously correct held-out questions.
- All three policies accepted those useful revisions. This round does not demonstrate an advantage of full RAVEL over hard gates.
- Accuracy-only accepted a researcher-injected development-answer memorization mutation; hard gates and RAVEL rejected it. This supports the value of basic checks under the tested attack, rather than establishing the value of every RAVEL component.
- Nineteen of 36 proposal slots produced missing or unloadable code, so proposer reliability remains a bottleneck. Slots are not independent samples: some conditions share proposals.
- The seed and accepted improved revisions followed injected instructions on all five held-out injection cases. The current relative injection gate allows an existing vulnerability to persist.

Round 2 adds a preliminary benefit/cost comparison:

- In clean seed 0, accuracy-only and hard gates accepted a revision that reduced held-out accuracy from 42/72 to 41/72. RAVEL rejected it through its regression gate. The same candidate appeared in the adversarial condition; this is not independent replication.
- In noisy seed 0, accuracy-only and hard gates accepted a revision that reduced accuracy from 42/72 to 40/72; RAVEL rejected it through its regression gate.
- In noisy seed 1, accuracy-only and hard gates accepted a revision that improved accuracy from 50/72 to 52/72. RAVEL rejected it as statistically insignificant. Although this misses the predefined three-answer beneficial threshold, it is still an observed positive gain and should be reported.
- In noisy seed 2, simpler policies accepted changes with unchanged held-out accuracy and reduced tokens; RAVEL retained its prior revision. Accuracy alone does not capture every potential benefit.
- Twenty-nine of 40 round-2 proposal slots ran successfully, compared with 17 of 36 in round 1. These are descriptive counts with shared proposals.

These observations concern only the first two completed rounds. They establish neither overall RAVEL superiority nor statistical significance of policy differences. Recompute the summary from final logs before manuscript use. Improvements occurring in the noisy condition do not establish that noise caused the improvements. Existing prompt-injection vulnerabilities also preclude broad security claims.

## Deferred extension: central research question

The remainder preserves the earlier scoped-acceptance idea for later consideration. It is contingent on the decision point above, not a commitment to implement every component.

Instead of asking only “Should this revision be accepted?”, ask:

> For which inputs, capabilities, and operating conditions does the evidence justify using this revision instead of the incumbent?

The proposed method jointly evaluates a patch and an explicit applicability rule. It may accept a patch within a limited scope, request more evidence, or reject it. Outside that scope, the incumbent remains the default, subject to independent security requirements.

Working title: **RAVEL: Scope-Constrained Acceptance of Agent Harness Revisions**.

## Proposed mechanism

### 1. Explicit patch claims and independently controlled routing

The proposer supplies:

- A small patch.
- A proposed applicability rule, such as Arabic financial lookups.
- A statement of the intended improvement and required capabilities.

Treat every claim as a hypothesis. Freeze and evaluate the patch and router together. The deployment controller, rather than the patch itself, determines whether the patch is eligible to run.

The existing additive-handler format is a starting point, but it is not sufficient: a handler currently decides when it fires, and helpers can collide with incumbent names. Use separate namespaces and restrict capabilities for each patch. Include router failures, scope-boundary errors, fallback behavior, latency, and token use in evaluation.

Scope selection must use information available at execution time. Do not use hidden task-family labels as a deployment oracle. Explicitly evaluate ambiguous and out-of-scope inputs.

### 2. Fresh tests targeted at the claimed improvement

For an Arabic financial lookup patch, generate new cases that vary company, year, metric, phrasing, and financial values. Test neighboring cases such as mixed-language questions, parent-company requests, and unrelated portfolio requests.

Generate new financial worlds as well as new wording. A memorized answer should fail when underlying values change. Verify generated test labels with deterministic oracles where possible.

Maintain separate stages:

1. Development of the patch and scope.
2. Fresh acceptance evaluation of the frozen patch/router.
3. Final held-out evaluation.

Do not reveal acceptance failures and then reuse those same cases as independent evidence for a revised patch. Targeted testing must also retain representative coverage of the overall deployment distribution; passing only a narrow challenge set is insufficient.

### 3. Controlled fault interventions

The current policy removes fault-affected items from some comparisons. This can discard meaningful evidence because a candidate's tool choices can affect whether it encounters a fault.

Evaluate parent and candidate under externally specified, matched scenarios:

- No injected faults.
- Defined timeout schedules.
- Defined schema changes or stale-data conditions.

Specify how fault schedules align when programs make different tool calls; using the same random seed alone is insufficient. Measure normal quality and robustness separately. Give credit for effective retries while accounting for their costs, and expose fragile dependencies introduced by revisions.

This tests explanations for an improvement instead of simply excluding observations with faults. Do not describe effects as causal without specifying the intervention and identification assumptions.

### 4. Search-wide evidence control

Independent per-candidate significance thresholds do not by themselves establish an error guarantee across adaptive candidates and rounds.

Begin with a transparent protocol: freeze candidate/router pairs before fresh acceptance batches, allocate a statistical error budget across candidates and rounds, and preserve an untouched final evaluation. Account for scope selection and repeated testing. Reusing a calibration set after adaptive feedback requires additional justification; a multiple-testing correction alone does not remove that dependence.

Consider sequential methods only after establishing a valid simple baseline. State distributional assumptions and distinguish regression-risk bounds from evidence of improvement. Do not claim guarantees under arbitrary distribution shift.

### 5. Absolute security requirements alongside relative preservation

Separate two kinds of requirements:

- Capability restrictions enforced by the broker, such as preventing unauthorized portfolio reads regardless of what generated code requests.
- Behavioral requirements measured on fresh probes, such as an upper bound on injection-following risk.

“No worse than the incumbent” is insufficient when the incumbent is already vulnerable. Falling back to a vulnerable incumbent does not establish safety. If neither path meets the required contract, abstain or route to an independently constrained workflow.

Probe results are evidence on tested distributions, not universal security proofs. Report abstention and coverage so safety cannot be improved invisibly by refusing everything.

## Potential contribution and prior art

The individual ingredients are not new:

- [Safe Policy Improvement with Baseline Bootstrapping](https://arxiv.org/abs/1712.06924) uses baseline behavior in uncertain regions in offline reinforcement learning.
- [Learn then Test](https://arxiv.org/abs/2110.01052) frames statistical risk control through hypothesis testing.
- [Meta-Harness](https://arxiv.org/abs/2603.28052) studies optimization of model harnesses.

The potential contribution is the joint treatment of executable harness patches, independently evaluated applicability scopes, capability restrictions, and controlled fault interventions under an explicit evaluation budget.

This is a novelty hypothesis, not a verified first-of-its-kind claim. Before committing to that framing, review work on selective prediction, model routing, safe policy improvement, program repair, regression-test selection, adaptive evaluation, and harness optimization. Scoped fallback alone should not be presented as novel.

## Main hypothesis

> Under equal total evaluation budgets, accepting revisions within independently validated scopes preserves more useful improvements at a given regression limit than accepting or rejecting revisions globally.

Secondary questions:

- Does targeted evidence acquisition reduce evaluation cost at a fixed decision quality?
- Do controlled fault interventions improve decisions relative to dropping fault-affected cases?
- What additional benefit remains beyond simple hard gates and a simple fixed router?
- When is scope estimation too unreliable or too expensive to help?

## Decisive experiment

Compare at least:

| Method | Acceptance behavior |
| --- | --- |
| Accuracy-only | Global acceptance based on development gain |
| Hard gates | Global acceptance with basic constraints |
| Current RAVEL | Global acceptance with statistical gates |
| Scoped RAVEL | Acceptance within a jointly evaluated applicability scope |

Include a simple fixed-scope routing baseline to test whether learned or proposed scope selection adds value. Match or explicitly account for proposal, repair, routing, solver, label, and evaluation budgets.

Use both naturally generated revisions and a separately labeled controlled pool. The controlled pool should contain beneficial, neutral, and harmful patches, including patches that improve one family while harming another. It diagnoses selector behavior; it cannot alone establish autonomous adaptation performance.

Report useful gains retained, regressions, violations, coverage, abstention, routing errors, token use, and latency. Report real latency separately from modeled latency. Use appropriate unit-level uncertainty estimates because candidates share parents and evaluation cases.

Key ablations: global versus scoped acceptance; simple versus proposed router; representative versus targeted evaluation under equal budgets; fault filtering versus interventions; per-candidate versus search-wide testing; relative versus absolute security requirements.

## Conditional extension steps after the contribution review

1. Finish and freeze the current study; analyze all completed rounds before changing the method.
2. Establish whether full RAVEL differs materially from hard gates and inspect where each gate affects useful and harmful revisions.
3. Confirm useful general improvements with development-only diagnostic controls, and assess proposer validity and output truncation separately from selection quality.
4. Only if the literature comparison and completed study justify an extension, prototype scoped acceptance with isolated patch namespaces and an explicit router. Start with a small controlled study containing mixed-benefit patches.
5. Compare against global hard gates and a simple routing baseline under matched budgets.
6. Expand to targeted evidence acquisition and controlled fault interventions only if the initial comparison supports the direction.
7. Freeze the new protocol before confirmatory experiments and maintain a fresh final test set. Previously inspected test cases are development evidence for the next study.

## Conditional extension decision criteria

Continue toward a scoped-method paper if scoped acceptance retains more useful gains at comparable regression and security limits, with costs and abstention accounted for, across more than one narrow setting.

If simple routing or hard gates perform equally well, report that result rather than attributing value to extra machinery. If the proposer still rarely generates useful revisions, distinguish candidate-generation limitations from acceptance-policy limitations.

The intended contribution is evidence about when and where revisions deserve acceptance, not a predetermined claim that a more complex RAVEL must win.
