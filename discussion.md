2609.35738v1.pdf
PDF
I would like you to find practicle flaws and shortcoming in this paper

Worked for 1m 9s
Critical Review: Practical Flaws and Shortcomings of “Harness Learning Enables Generalizable Test-Time Adaptation”
Alvin Zhang et al. · arXiv:2609.35738v1 · September 2026 · 36 pages

Overall assessment
The paper presents an interesting engineering idea: instead of modifying an AI model's weights whenever performance needs to improve, train another model to modify the executable software that controls the AI agent.

This software, called the harness, determines which tools the agent uses, how it retrieves information, how it reasons across steps, and how it generates answers.

The researchers demonstrate measurable improvements on reasoning and multi-hop question-answering benchmarks.

However, there is a considerable difference between demonstrating that an AI can improve its own harness on benchmarks and demonstrating that it can safely, economically, and reliably maintain a production system.

My central criticism is that the paper demonstrates successful automated harness optimization under controlled conditions, but does not establish practical autonomous adaptation in real-world software systems.

My assessment of the research

Promising, not production-proven
Research concept

8/10

Experimental evidence

7/10

Real-world generalization

4/10

Operational feasibility

3/10

Production safety

2/10

Economic justification

3/10

My subjective engineering-readiness ratings, not scores reported by the authors.
1. The most significant practical flaws
These are prioritized by potential impact on real-world deployment.

1. Allowing AI to modify executable orchestration introduces serious security risks

Critical
The proposer modifies executable Python harness code, potentially affecting model calls, tool usage, and control flow.

In production, this creates risks such as unauthorized API calls, accessing sensitive information, introducing unsafe code paths, or removing existing security controls.

The paper describes guarded execution during experiments, but it does not demonstrate a production security architecture for approving, signing, and deploying AI-generated revisions.

Practical failure: An agent optimizing a financial research workflow could alter a data-access function to retrieve restricted portfolio information or bypass authorization checks without reducing its benchmark score.

What is missing: Capability-limited sandboxes, policy-preservation checks, immutable security controls, strict tool permissions, and human approval for sensitive changes.

Relevant sections: 4.2, Appendix B.2 and Appendix D.3.
2. Optimizing benchmark accuracy is not equivalent to optimizing system quality

Critical
The main reward is question-answering performance plus a validity or execution bonus. The QA experiments principally measure normalized exact match.

That leaves major production concerns outside the optimization objective: latency, cloud expenditure, factual citation quality, security, maintainability, and operational resilience.

Practical failure: A revised harness achieves 85% accuracy instead of 80% but performs six additional LLM calls per request, doubling latency and materially increasing cost.

From a benchmark perspective, this is an improvement. From a commercial perspective, it might be a regression.

What is missing: Multi-objective evaluation with explicit latency, cost, reliability, security, and quality constraints.

Relevant sections: 4.1–4.3, Equation 6, and Appendix D.2.
3. The approach assumes that correct feedback is available

Critical
The experiments have questions with known answers and automated graders. Execution reports can even show the agent whether its answers are correct and which supporting documents were missed.

Most real-world applications do not have this advantage.

For example, consider asking an investment agent whether a company's financial performance signals long-term improvement. There may be no immediate objectively correct answer, and financial interpretations can remain disputed.

Practical failure: The system modifies its retrieval strategy based on erroneous or subjective feedback and reinforces the wrong behavior.

What is missing: Robust learning from weak or delayed feedback, uncertain labels, expert validation, and measures of evaluator reliability.

Relevant sections: 4.1 and Appendix D.2–D.3.
4. Improvements on one class of tasks can introduce regressions elsewhere

High
The revised harnesses are scored on bounded question sets. There is no demonstrated production-wide regression-testing system across unrelated business capabilities.

A revision that improves multi-hop retrieval could damage simple lookups, Arabic-language processing, structured numerical queries, or API integration behavior.

Practical failure: A harness modification improves answers to complex financial questions but causes previously correct single-company price queries to fail.

What is missing: Cross-task regression suites, protected capabilities, statistical acceptance criteria, and rollback mechanisms.

Relevant sections: 4.2, 5.2–5.3 and Appendix B.1.
5. The computational and economic cost of adaptation is not justified

High
In the QA evaluation, a revision run performs ten rounds, with eight candidate revisions per round. Candidate harnesses are scored on development questions, and retained harnesses are separately evaluated.

This is an expensive optimization process compared with ordinary inference. Although much of this can be performed offline, that does not eliminate its cost.

The paper compares candidate counts but explicitly acknowledges that compute and feedback are not fully matched in its independent-versus-sequential comparison.

Practical failure: A company spends substantial GPU time improving a workflow whose additional accuracy provides little measurable business benefit.

What is missing: Wall-clock adaptation costs, inference cost before and after revision, GPU-hours, and return-on-investment or break-even analysis.

Relevant sections: 5.3 and Appendix D.3–D.4.
2. Weaknesses in the experimental methodology
Some shortcomings are particularly important because they affect how strongly we can interpret the paper's conclusions.

Weakness

Evidence in paper

Why it matters

Exclusion of difficult benchmarks

Appendix B.1 excludes five unseen reasoning families from the main figures, while separately reporting all 26

The headline 21-family average presents a more favorable subset

Simplified environments

Reasoning Gym puzzles and Wikipedia-based QA

Real production workflows are substantially more complex

Unequal optimization budgets

Section 5.3 acknowledges unmatched compute and feedback

Improvements cannot be attributed cleanly to sequential adaptation alone

Repeated development data

Appendix D.3 permits questions to recur across rounds

Optimization can become increasingly specialized to development questions

Different retrieval environments

HotpotQA uses 5.23 million Wikipedia abstracts; MuSiQue and 2Wiki use much smaller pooled paragraph corpora

Transfer results are affected by changes in retrieval difficulty

Limited model diversity

The experiments use Qwen 4B proposers and Qwen 4B/8B solvers

Cross-model and cross-provider transfer remains unestablished

Weak evidence of improvement from multistep training

Section 5.4 finds inconsistent or nearly identical outcomes

The additional training complexity has not demonstrated dependable value

A particularly important detail: the excluded task families
Page 16, Appendix B.1, reveals that five difficult unseen families were omitted from the main figures.

The paper does provide aggregate results when those families are included:

Single-step scores across all 26 unseen reasoning families
Appendix B.1; average held-out score including five families excluded from the main figures.

0
0.15
0.3
0.45
0.6
Base
SFT
RL
Teacher
Base: Average score 0.282
SFT: Average score 0.415
RL: Average score 0.528
Teacher: Average score 0.501
The headline result is 0.62 for the trained proposer across 21 unseen families. Including the five additional difficult families lowers that to 0.528.

This does not invalidate the research: the improvement over Base remains substantial. However, it demonstrates why benchmark selection matters and why deployment decisions should not rely only on the headline figures.

A second subtlety is that the paper reports oracle best-of-N results, where the best candidate is identified using held-out test performance. The authors correctly label these oracle statistics, but this is not an available selection mechanism in production, where the true test answers are unknown.

3. Other important engineering shortcomings
6. The system is learning to work around a limited set of benchmark structures
On Reasoning Gym, the researchers find that trained harnesses frequently introduce Python interpreter loops. The paper reports that 48% of the supervised examples use this structure.

This raises a question: Is the model learning a generally useful harness-adaptation capability, or is it learning to recognize benchmark categories and introduce familiar solutions?

Both may be true.

The evidence supports transfer across unseen benchmark families, but not unrestricted generalization across arbitrary real-world workflows.

For example, adding Python execution to solve mathematical puzzles is fundamentally different from improving a financial research agent that must coordinate historical data, permissions, live market updates, and regulatory disclosures.

7. Maintaining AI-generated code could become progressively more difficult
The approach repeatedly edits existing harness code.

Yet successful execution and question accuracy do not guarantee that the code remains understandable, maintainable, or architecturally coherent.

Over many rounds, an AI-generated harness might accumulate unnecessary conditions, duplicate logic, complex exception handling, and hidden dependencies.

The paper investigates structural patterns but does not establish long-term maintainability across sustained production evolution.

A production implementation would require code-quality gates, complexity limits, duplication checks, automated regression tests, and versioned releases.

8. There is no demonstrated long-term stability of adaptation
The paper primarily evaluates five or ten revision rounds.

That is useful for assessing short-term adaptation, but it is insufficient to show continual improvement over months of operation.

Imagine a harness modified 500 times, with new tool APIs, model versions, and data formats introduced along the way.

Would it still perform reliably? Would it preserve its previous improvements? Would the proposer remain effective as the codebase diverges from the training distribution?

These remain open questions.

9. The paper does not establish compatibility with changing model behavior
The solver is deliberately frozen.

That is scientifically useful because it isolates harness improvements from model improvements. However, production systems frequently change their underlying models.

A harness optimized for one model's tool-calling behavior may perform worse after switching to another model.

The paper does not demonstrate durable revision performance across substantial solver upgrades or different model providers.

10. The proposer cannot independently investigate problems
Appendix F acknowledges that the proposer receives externally generated execution reports and prescribed revision prompts.

It does not autonomously decide which tests to run, inspect the complete system, or investigate the underlying reason for a failure before proposing a change.

This is a meaningful limitation.

An experienced engineer diagnosing a failing workflow might inspect logs, database queries, API responses, recent deployments, and environmental differences before making a code change.

The paper's proposer is much more constrained. It learns to edit from prepared feedback, rather than demonstrating a complete engineering investigation process.

4. What happens when this approach encounters real financial systems?
Consider an AI assistant using company financial statements, market prices, regulatory disclosures, and financial calculations.

Production scenario

What can go wrong with the proposed approach

Required additional protection

A stock price is outdated

The harness changes its retrieval logic when the actual problem is stale upstream data

Data freshness verification

Two financial statements disagree

The agent optimizes toward a benchmark answer instead of resolving reporting-period or restatement differences

Source lineage and accounting validation

The model gives a wrong financial ratio

The proposer changes prompting instead of fixing the underlying calculation

Deterministic financial calculation tools

An external API times out

Revisions introduce excessive retries and overwhelm the provider

Circuit breakers, retries with limits, and rate controls

An Arabic query fails

Optimization toward English-language evaluation cases causes regressions

Bilingual regression testing

A retrieved document contains malicious instructions

The agent changes workflow behavior based on untrusted content

Prompt-injection defenses and isolated permissions

A financial API returns confidential data

The answer is correct, but access policies have been violated

Authorization and data classification enforcement

The important distinction is that not every incorrect AI response indicates a defective harness.

Errors may originate from data quality, missing information, upstream APIs, ambiguous questions, model limitations, or flawed evaluation criteria.

The proposed system has no demonstrated comprehensive root-cause classification that reliably separates these failure sources.

That is a fundamental practical limitation.

5. How I would redesign the approach for production
Rather than allowing a proposer to freely rewrite a production harness, I would introduce a controlled adaptation architecture.

Production AI Agent

Live executions, logs, errors, performance metrics

Failure Classification

Data · Model · Retrieval · Tool · Harness · Infrastructure

Harness Revision Proposer

Generates candidate changes without production permissions

Security & Code Validation

Sandbox, permissions, static checks

Regression & Quality Tests

Accuracy, cost, latency, reliability

Release Gate

Reject · Request review · Approve for canary

Canary Deployment and Monitoring

Gradual rollout · Automatic rollback on regression

I would also separate two types of adaptation:

Runtime adaptation: Selecting between approved retrieval strategies, adjusting search depth, or using different predefined tools. This can be relatively safe and reversible.

Structural adaptation: Generating or modifying executable code, changing interfaces, or introducing new tools. This should follow normal software release controls.

The paper largely concentrates on structural adaptation. In my view, runtime adaptation would be the more practical starting point for many commercial systems.

6. The experiments I would ask the authors to conduct
If I were reviewing this work for practical impact, I would request the following five experiments before accepting its broader deployment claims.

Experiment

What it would reveal

Cost-normalized comparison against fixed tool loops, prompt optimization, retrieval tuning, and standard LLM-assisted coding

Whether trained harness revision is economically better than simpler engineering methods

Long-running adaptation over 100–500 revision rounds with periodic API and data changes

Whether improvements persist or produce cumulative regressions

Security adversarial testing with prompt injection, malicious tool responses, and restricted APIs

Whether arbitrary executable edits can be made safe

Realistic mixed-workload benchmark combining financial QA, API outages, multilingual requests, and changing source data

Whether improvements generalize to complex applications

Noisy-feedback experiment with incorrect labels, delayed answers, and subjective evaluations

Whether learning remains robust without perfect graders

Each experiment addresses a different gap. Together, they would make the paper substantially more convincing from a systems-engineering perspective.

7. Questions that challenge the central premise
Three deeper questions remain unresolved.

First, when does a problem require harness learning rather than ordinary software engineering?

The paper demonstrates that training a proposer can improve harness revisions. It does not sufficiently establish the conditions under which this approach is preferable to simpler alternatives such as a well-designed tool loop, deterministic retrieval logic, or conventional automated testing and code generation.

Second, who validates the validator?

A central assumption is that the execution feedback provides a useful signal about quality. But when performance depends on subjective judgments, incomplete data, or complex financial interpretations, the evaluation mechanism itself can be wrong.

Training a proposer to optimize an unreliable evaluator may create a system that becomes better at satisfying the evaluator without becoming more useful or correct.

Third, is the harness learning a reusable engineering principle, or merely accumulating successful task-specific fixes?

The paper provides evidence of transfer to unseen reasoning families and QA datasets. However, showing that an agent learns broad software-engineering principles would require substantially more diverse environments, longer adaptation histories, and tests against truly novel operational constraints.

Final verdict
The paper's strongest contribution is showing that a relatively small model can learn to propose better executable workflow changes, and that these changes can sometimes accumulate productively across rounds.

That is a meaningful result.

But the engineering claim I would be willing to accept is narrower than the broader vision of continually learning agents.

What the evidence supports: Learned harness revision can improve accuracy and revision reliability on the tested benchmark families, including some unseen tasks.

What remains unproven: That this approach is cost-effective, safe, stable over long periods, or superior to simpler techniques in production environments.

What I would build: A harness optimization service that proposes and tests changes offline, with explicit release gates, rather than an autonomous system that continuously modifies its own production execution logic.

The criticism I would put directly to the authors is:

Your experiments demonstrate that a learned model can improve executable harnesses under controlled, verifiable conditions. But how do you prevent the optimization mechanism from producing systems that are more accurate on measured tasks while simultaneously becoming less secure, less maintainable, more expensive, or less reliable on unmeasured tasks?

For me, answering that question is the difference between an interesting AI research technique and a trustworthy engineering methodology.

Can we complete the shortcoming of this paper and produce another paper with example or expirements of our own ?

Worked for 1m 4s
Research Proposal: From Harness Learning to Production-Grade Self-Improving AI Agents
Yes. We can develop a follow-up research paper with an original method, a working implementation, reproducible experiments, and measured results.

I think this is a worthwhile research direction because the original paper, Harness Learning Enables Generalizable Test-Time Adaptation, establishes something important: a trained proposer can improve the executable workflows of a frozen language model.

What it does not establish is whether that adaptation remains safe, economical, reliable, and maintainable under realistic operating conditions.

Our paper can focus on exactly that missing layer.

1. Proposed research contribution
Beyond Accuracy: Risk-Aware and Cost-Constrained Harness Learning for Production AI Agents
Alternative title: From Harness Learning to Reliable Self-Evolving AI Systems

The central hypothesis would be:

Harness adaptation that optimizes accuracy alone is insufficient for real-world deployment. A risk-aware adaptation framework that combines performance optimization, security constraints, regression validation, and cost-aware candidate selection can produce more reliable and economically efficient agent improvements.

We should aim to contribute three things:

A reproducible failure benchmark showing when conventional harness optimization produces undesirable outcomes despite accuracy gains.

A new adaptation algorithm that improves harnesses while preserving constraints on cost, security, latency, and previously working functionality.

Experimental evidence comparing the original approach, simpler optimization baselines, and our proposed method under equivalent resource budgets.

The contribution should be more than wrapping an AI code editor in a CI/CD pipeline. We need a genuinely measurable algorithmic improvement.

2. Proposed experimental framework
I would call the system RAVEL — Risk-Aware Validated Evolution of LLM Harnesses (working research name).

Task and Environment

Financial QA · API integration · Reasoning · Retrieval

Failure Diagnosis

Classify data, tool, retrieval, model, and harness problems

Harness Revision Proposer

Generate candidate patches and predict their risks

Hard Constraints

Permissions, policy, sandbox, code validity

Multi-Objective Evaluation

Accuracy, cost, latency, reliability

Constrained Candidate Selection

Reject unsafe revisions; select within an explicit budget

Validated Harness

Versioned revision with measurable improvement and rollback support

The algorithm should select a revised harness only when it passes hard requirements and provides a favorable balance of accuracy and operational cost.

An initial formulation could be:

max
⁡
h
A
(
h
)
−
λ
C
C
(
h
)
−
λ
L
L
(
h
)
h
max
​
 A(h)−λ 
C
​
 C(h)−λ 
L
​
 L(h)
Subject to:

S
(
h
)
=
1
R
(
h
)
≤
ϵ
R
C
(
h
)
≤
B
C
L
p
95
(
h
)
≤
B
L
​
  
S(h)=1
R(h)≤ϵ 
R
​
 
C(h)≤B 
C
​
 
L 
p95
​
 (h)≤B 
L
​
 
​
 
Where:

A
A: answer quality or task performance

C
C: execution cost

L
L: latency

S
S: satisfaction of required security and policy checks

R
R: regression rate on protected tasks

B
C
,
B
L
B 
C
​
 ,B 
L
​
 : deployment budgets

This is a starting formulation, not yet a novel result. The research work is in designing an efficient method for estimating these quantities under uncertainty, selecting candidates, and learning better revisions.

3. Our experimental plan
I would start with four experiments, each designed to expose a limitation and then measure whether RAVEL can address it.

Experiment A — Security-preserving adaptation

Generate candidate harness revisions in an isolated container. Introduce adversarial tool outputs, attempts to bypass authorization, and unsafe code modifications.

Compare ordinary accuracy-based selection with policy-constrained selection.

Measurements: Attack success rate, accepted unsafe modifications, clean-task accuracy, and false rejection rate.

Experiment B — Cost-aware harness evolution

Create multiple retrieval workflows: single call, multiple retrieval hops, adaptive search depth, and answer verification.

Compare the original score-maximization approach with a cost-constrained optimizer.

Measurements: Answer accuracy, total tokens, API cost, p50/p95 latency, and accuracy gained per dollar.

Experiment C — Regression-resistant adaptation

Give each agent several capabilities and optimize it for only one subset.

Evaluate whether improvements damage tasks that were already solved correctly. Repeat adaptation over many rounds.

Measurements: New-task accuracy, previously solved task retention, regression rate, code complexity, and cumulative improvement.

Experiment D — Adaptation under unreliable feedback

Introduce noisy labels, stale retrieved information, intermittent API errors, and incomplete feedback.

Test whether failure classification and confidence-aware candidate selection prevent harmful revisions.

Measurements: Accuracy under noise, wrong-change rate, recovery time, and degradation relative to clean feedback.

For each experiment, we should run at least these baselines: an unchanged seed harness, a general-purpose LLM code-revision proposer, accuracy-only harness optimization, and RAVEL. If we can reproduce the original trained proposer, that should be a separate baseline rather than assuming an ordinary LLM editor is equivalent.

A good protocol would use disjoint adaptation, validation, and final test sets; repeated random seeds; confidence intervals; and matched total compute and feedback budgets.

4. An original financial-agent testbed
We could make this research especially useful by building a financial-agent benchmark, rather than relying exclusively on mathematical puzzles or Wikipedia QA.

For example, a synthetic dataset could contain:

Scenario

Expected verified behavior

Compare two companies' revenue growth

Retrieve the correct periods and calculate growth

Restated financial results

Prefer the appropriate revised statements and disclose restatements

Missing trading session

Avoid treating stale prices as current

Corporate announcement contradicts older data

Resolve dates and cite the appropriate source

Arabic financial question

Preserve semantic and numerical correctness across languages

Unauthorized portfolio request

Refuse access even when a correct answer is technically obtainable

Financial data API failure

Recover safely, or report insufficient data without inventing values

This would be a controlled test environment using synthetic companies and accounts, with deterministic expected calculations and a fully auditable ground truth.

Later, we could extend evaluation to real public Saudi financial disclosures and XBRL records, keeping any proprietary Argaam data or internal systems separate from the published research.

5. Important novelty check
We should not claim that cost-aware or safe harness optimization is entirely unexplored.

A related 2026 paper, Rethinking the Evaluation of Harness Evolution for Agents, already examines matched-budget comparisons and limited generalization. 

arXiv

Another paper, EVOHARNESSBENCH, investigates competence loss as an agent's harness evolves. 

arXiv

These papers actually strengthen our motivation, but they mean that simply demonstrating benchmark overfitting or regression would not be enough for a new contribution.

Our potential novelty should be the combination of failure-aware adaptation, uncertainty-aware constrained candidate selection, and independently evaluated safety and cost guarantees—and, more importantly, experimental evidence that this combination outperforms existing methods.

We can also consider formalizing an adaptation failure budget: how much measured degradation is allowable before an automatically proposed change must be rejected. The usefulness of that formulation would need to be demonstrated experimentally.

6. How we turn this into a publishable paper
01

Reproduction and baseline validation

Reproduce selected results from the original paper or implement a clearly labeled approximation if the original training artifacts are unavailable. Establish test datasets, metrics, and compute budgets.

Proposed duration: 1–2 weeks

02

Build the RAVEL prototype

Implement the isolated revision engine, fault classifier, policy checks, evaluation runner, constrained selector, and versioning mechanism.

Proposed duration: 2–3 weeks

03

Execute controlled experiments

Run the four experiments, record every candidate revision, and analyze accuracy, safety, efficiency, regressions, and statistical uncertainty. Include ablations to establish which RAVEL components actually contribute.

Proposed duration: 2–3 weeks

04

Write and release the paper

Prepare methodology, results, limitations, reproducibility package, diagrams, experiment configurations, and a submission-ready manuscript.

Proposed duration: 1–2 weeks

A reasonable initial estimate is 6–10 weeks, assuming one primary engineer/researcher, usable compute, and no major reproduction blockers.

Our deliverables would be a research paper, a GitHub repository containing the experimental framework, synthetic benchmark datasets, experiment scripts, result tables, and reproducible charts.

Crucially, we should write the introduction and methodology now, but leave the results and conclusions open until we run the experiments. We should publish negative findings too if the proposed method does not outperform a simpler baseline.

7. Where I recommend we begin
I recommend starting with Experiment C (regression-resistant adaptation) and Experiment B (cost-aware optimization). They are comparatively easy to measure, have direct production relevance, and provide a foundation for the harder security and noisy-feedback experiments.

The project can initially run entirely on open-source models with synthetic datasets, avoiding dependence on Argaam's live infrastructure.

Before designing the implementation in detail, there is one important choice:

Which research scope should we use?


Independent public research (recommended)

Fully open-source framework and synthetic/public datasets, suitable for academic publication.


Argaam-oriented applied research

Develop the same scientific framework with financial-agent workflows relevant to Argaam, adding public reproducible tests.


Hybrid

Public benchmark and paper, plus a separate private Argaam case study.

My goal would be a paper that doesn't merely criticize the original research, but provides reproducible evidence about when self-improving agents can be trusted, when they should reject their own proposed improvements, and what those safeguards cost.

Proceed with independent public research. Create the detailed RAVEL research specification, experiment design, repository architecture, and first implementation plan.

Worked for 2m 46s
RAVEL — Research Specification v0.1
Independent, open-source research · 19 October 2026 · Proposed study, not yet experimentally validated

1. Research identity
RAVEL: Risk-Aware, Budget-Constrained, and Regression-Preserving Evolution of LLM Agent Harnesses
Research question: Can an automated harness adaptation method deliver useful accuracy improvements while respecting fixed computation budgets, avoiding previously solved-task regressions, and preventing unsafe modifications?

The main contribution will not simply be another harness editor. It will be a controlled, auditable method for deciding which AI-generated harness modifications deserve to be accepted.

The starting point is the uploaded Harness Learning Enables Generalizable Test-Time Adaptation paper. It trains a proposer to revise executable harnesses using execution feedback and evaluates transfer across reasoning and multi-hop QA tasks. Its immediate revision rewards primarily capture task quality and execution validity. Our work will investigate the operational properties that this reward does not explicitly capture.

Research hypotheses
ID

Testable hypothesis

What would falsify it

H1

RAVEL reduces accepted unsafe or regressive revisions compared with accuracy-only evolution

No statistically distinguishable reduction

H2

RAVEL achieves better cost–quality trade-offs under matched optimization budgets

Simpler optimization achieves the same or better Pareto frontier

H3

Regression-aware selection improves retention of previously solved tasks over repeated revisions

Comparable regression rates with and without retention gates

H4

Fault-aware adaptation reduces unnecessary harness changes caused by upstream failures

Fault diagnosis introduces more errors than it prevents

H5

Improvements transfer to held-out task templates, environments, and solver models

Gains disappear outside the adaptation distribution

These are hypotheses rather than claims. In particular, H1 should not be interpreted as a guarantee that passing static checks makes executable code secure.

2. Novelty and prior research
The relevant literature makes our scope clearer.

Harness Learning Enables Generalizable Test-Time Adaptation motivates training a proposer to adapt harnesses from execution feedback.

Rethinking the Evaluation of Harness Evolution for Agents already questions unmatched optimization budgets and benchmark-specific overfitting. Its findings mean fair comparison cannot be treated as our novel contribution. 

arXiv

HarnessEvolve already uses reference trajectories, quality gates, and retention-based performance gates. We should not claim to have invented regression gating or separated evaluation. 

arXiv

HarnessDev evaluates harness creation and evolution using capability and token efficiency, and reports unstable gains and limited transfer. 

arXiv

Our defensible research opportunity is to investigate uncertainty-aware constrained acceptance, selective fault diagnosis, and operationally realistic safety/cost evaluation as one cohesive method. This combination still requires a fuller systematic literature review before claiming novelty.

3. Scope of the independent study
Included

Open-source code, reproducible synthetic environments, fixed solver models, Python harness revisions, public benchmark extensions, and independent held-out testing.

Excluded initially

Production deployment, proprietary datasets, changing model weights, real customer data, claims of formally verified security, and autonomous modifications to external services.

We will use a two-layer research design: a deterministic, inexpensive experimental environment to verify evaluation logic and reproduce failure cases, followed by actual LLM-generated harness revisions to determine whether the findings transfer beyond handcrafted examples.

4. Experiment design and evaluation protocol
We will run four experiments, in this order:

Experiment

Main variables

Primary evidence

E1: Regression preservation

Revision rounds, protected tests, selection policy

Previously correct behaviors retained

E2: Cost and quality

Token budget, retrieval depth, selection method

Accuracy–cost Pareto frontier

E3: Unsafe modification resistance

Malicious patches, untrusted inputs, policy checks

Rate of accepted unsafe modifications

E4: Fault diagnosis

Noisy labels, tool failures, stale sources

Unnecessary revision rate and recovery performance

Dataset construction
For the initial pilot, I propose five task families: numerical reasoning, multi-hop retrieval, structured financial calculations, multilingual QA, and tool/API workflows.

The prototype benchmark will use synthetic fixtures with deterministic answers. For the full study, a preliminary target is 200 adaptation cases, 200 validation cases, and 500 hidden test cases per family, subject to a power analysis.

Most importantly, we will split by question generator and task template, not merely by randomly dividing generated questions. Otherwise, a harness might effectively memorize a task pattern while appearing to generalize.

Comparison methods
Baseline

Description

B0

Immutable seed harness

B1

Repeated solver calls or best-of-N inference

B2

General-purpose LLM harness editing without execution feedback

B3

Accuracy-only propose, evaluate, and select

B4

Conventional hard-constraint selection without confidence estimates

B5

Full RAVEL method

Where possible, we will also evaluate the actual trained proposer from the original research. If its implementation or checkpoints are unavailable, we will explicitly distinguish our reconstruction from an exact reproduction.

Statistical rules
We should preregister the main outcomes and budgets before running the confirmatory experiments. Each method should receive comparable proposal counts, solver calls, feedback access, and total optimization expenditure.

The primary reporting will include paired differences and 95% confidence intervals, with multiple-comparison correction where relevant. At least five random seeds will be used in the pilot, with a target of ten for confirmatory results if feasible.

We will report failures and rejected revisions, not just final accuracy.

5. Proposed repository architecture
The complete research repository should evolve toward this structure:

ravel/

├── ravel/
│   ├── core.py               # Outcomes and acceptance rules
│   ├── harness/              # Executable harness protocol
│   ├── proposer/             # LLM revision policies
│   ├── diagnosis/            # Fault classification
│   ├── evaluation/           # Quality and confidence estimates
│   ├── security/             # Policy checks and sandbox adapter
│   ├── selection/            # Multi-objective optimization
│   ├── telemetry/            # Traces, usage and cost records
│   └── storage/              # Versioned candidates and runs
├── benchmarks/
│   ├── financial_qa/
│   ├── reasoning/
│   ├── tool_failures/
│   └── adversarial/
├── baselines/
│   ├── seed.py
│   ├── best_of_n.py
│   ├── accuracy_only.py
│   └── constrained.py
├── experiments/
│   ├── exp01_regression.py
│   ├── exp02_cost.py
│   ├── exp03_security.py
│   └── exp04_noisy_feedback.py
├── configs/
├── tests/
├── scripts/
├── results/
├── paper/
└── pyproject.toml

Target structure. The downloadable v0.1 scaffold implements only the first acceptance-policy components; the remaining modules are planned.
For implementation, I would use Python 3.11+, pytest, Pydantic, Hugging Face-compatible local or remote model adapters, and container-based isolated execution. SQLite is sufficient for the first experiment ledger; DuckDB or Parquet can handle analytical results.

Actual untrusted Python patches must execute in a separate hardened environment with disabled networking, restricted capabilities, resource limits, and no host secrets. A normal Python subprocess is not a sufficient security boundary.

6. First implementation sprint
PROPOSED FIRST 10 WORKING DAYS

Day 1–2

Establish baseline

Pin runtime and model versions, validate source licenses, define task schema and benchmark splits

Day 3–4

Build execution infrastructure

Implement harness interface, tool mocks, isolated execution, trace collection, and deterministic grading

Day 5–6

Implement comparison methods

Seed, best-of-N, accuracy-only selector, and hard-constraint baseline

Day 7–8

Build benchmark fixtures

Generate initial regression, cost, security, and failure-injection cases

Day 9

Execute pilot

Run a small matched-budget experiment and inspect false accepts, regressions, and failures

Day 10

Review and freeze

Publish reproducibility report, raw results, limitations, and revised confirmatory plan

Sprint acceptance criteria: By the end of this sprint, we should be able to submit candidate harness revisions, execute them under controlled conditions, collect complete results, explain accept/reject decisions, and reproduce those decisions from saved experimental artifacts.

The first pilot is primarily intended to validate the methodology and infrastructure. It is not expected to establish the paper's final scientific claims.

7. Initial research package
I've created a downloadable RAVEL starter repository, including a detailed research specification, an executable acceptance-policy prototype, illustrative candidate cases, and unit tests.

RAVEL Research Starter v0.1

Python source · Research protocol · Configuration · Tests · Paper outline

Download complete starter repository

Detailed Research Specification

Hypotheses, datasets, comparisons, statistics, algorithm, and acceptance criteria

Read RESEARCH_SPEC.md

Initial Demo Results

Illustrative acceptance and rejection cases; not actual LLM experiment results

View demo output

5 of 5 initial unit tests passed.

The current prototype implements a basic acceptance rule, budget limits, a one-sided Wilson confidence bound for measured regression rates, and rejection reasons. It does not yet implement an LLM proposer, fault classifier, real sandbox, or trained policy. The security verdict in the demo is mocked.

To run it locally:

python -m unittest discover -s tests -v
python -m experiments.demo

8. The next technical milestone
I recommend that the first substantive scientific result be a controlled study of regression-aware harness evolution under matched computation budgets.

This allows us to test an important question before spending resources on reinforcement learning:

Can a relatively simple, statistically cautious harness-selection algorithm outperform accuracy-only selection, or does its conservatism prevent useful adaptation?

Both outcomes are academically useful. If it succeeds, we can add fault diagnosis and learned candidate ranking. If it fails, we will understand which constraints are too restrictive and whether learning a better adaptation policy is justified.

The intended final product is not just a paper claiming that RAVEL is better. It is an open, reproducible investigation into whether and under what conditions AI agents can improve their own executable systems without sacrificing the properties that make those systems dependable.

