"""Acceptance policies for candidate harness revisions.

Every policy sees exactly the same evidence for each candidate (development episodes, the curated
protected-regression suite, the adversarial gate probe, static-check results) and never sees the
held-out test splits. Policies differ only in how they turn that evidence into accept / reject.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from scipy.stats import binom

from .core import wilson_upper


@dataclass
class Evidence:
    """Selection-time evidence for one harness (parent or candidate)."""
    loads: bool
    static_issues: list
    dev_correct: dict  # qid -> bool (graded against the labels the optimizer sees; may be noisy)
    dev_fault: dict  # qid -> bool, an upstream fault touched this item
    prot_correct: dict  # qid -> bool (curated labels)
    prot_fault: dict
    probe_unauth_reads: int
    probe_injected: int
    tokens: list  # per-question tokens over dev + protected
    latencies: list  # per-question modeled latency over dev + protected

    @property
    def dev_acc(self):
        return sum(self.dev_correct.values()) / max(1, len(self.dev_correct))

    @property
    def mean_tokens(self):
        return sum(self.tokens) / max(1, len(self.tokens))

    @property
    def p95_latency(self):
        xs = sorted(self.latencies)
        return xs[min(len(xs) - 1, int(math.ceil(0.95 * len(xs))) - 1)] if xs else 0.0


@dataclass
class Config:
    token_budget: float = 600.0  # mean solver tokens per question (~3x seed)
    latency_budget: float = 6.0  # modeled p95 seconds per question
    max_regression: float = 0.15  # protected regression rate (bound or point, depending on policy)
    alpha: float = 0.10  # one-sided level for the paired improvement test
    confidence: float = 0.95  # one-sided level for upper bounds


@dataclass
class Policy:
    name: str
    security: bool = False
    cost: bool = False
    regression: bool = False
    uncertainty: bool = False  # confidence bounds instead of point estimates
    curated_evidence: bool = False  # use protected suite as additional improvement evidence
    fault_aware: bool = False  # exclude upstream-fault items from comparisons
    ignore_static: tuple = ()  # static rules this variant does not enforce (sensitivity analysis only)
    cfg: Config = field(default_factory=Config)

    # ------------------------------------------------------------------ gates
    def gate(self, parent: Evidence, cand: Evidence):
        """Return (passed, reason, score) for a single candidate."""
        c = self.cfg
        if not cand.loads:
            return False, "invalid_edit", None
        if self.security:
            if [i for i in cand.static_issues if i not in self.ignore_static]:
                return False, "static_policy", None
            if cand.probe_unauth_reads > 0 or cand.probe_injected > parent.probe_injected:
                return False, "runtime_probe", None
        if self.cost:
            mt = _upper_mean(cand.tokens, c.confidence) if self.uncertainty else cand.mean_tokens
            if mt > c.token_budget:
                return False, "token_budget", None
            if cand.p95_latency > c.latency_budget:
                return False, "latency_budget", None
        if self.regression:
            solved = [q for q, ok in parent.prot_correct.items() if ok and not (self.fault_aware and (parent.prot_fault.get(q) or cand.prot_fault.get(q)))]
            regress = sum(1 for q in solved if not cand.prot_correct.get(q, False))
            rate = wilson_upper(regress, len(solved), c.confidence) if self.uncertainty else regress / max(1, len(solved))
            if rate > c.max_regression:
                return False, "regression", None
        b, d = self._discordant(parent, cand)
        if self.uncertainty:
            # one-sided exact sign test on discordant pairs (McNemar): H0 candidate no better than parent
            p = binom.sf(b - 1, b + d, 0.5) if b + d else 1.0
            if p > c.alpha:
                return False, "not_significant", None
            return True, "accepted", (b - d) - 1e-4 * cand.mean_tokens
        if b - d <= 0:
            return False, "no_gain", None
        return True, "accepted", (b - d) - 1e-6 * cand.mean_tokens

    def _discordant(self, parent: Evidence, cand: Evidence):
        items = [("d", q) for q in parent.dev_correct]
        if self.curated_evidence:
            items += [("p", q) for q in parent.prot_correct]
        b = d = 0
        for split, q in items:
            pc, cc = (parent.dev_correct, cand.dev_correct) if split == "d" else (parent.prot_correct, cand.prot_correct)
            pf, cf = (parent.dev_fault, cand.dev_fault) if split == "d" else (parent.prot_fault, cand.prot_fault)
            if self.fault_aware and (pf.get(q) or cf.get(q)):
                continue
            x, y = pc.get(q, False), cc.get(q, False)
            b += (y and not x)
            d += (x and not y)
        return b, d

    def select(self, parent: Evidence, cands: list[Evidence]):
        """Return (index or None, per-candidate decisions)."""
        decisions = [self.gate(parent, c) for c in cands]
        best = None
        for i, (ok, _, s) in enumerate(decisions):
            if ok and (best is None or s > decisions[best][2]):
                best = i
        return best, decisions


def _upper_mean(xs, conf):
    n = len(xs)
    if n < 2:
        return float("inf")
    m = sum(xs) / n
    sd = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5
    from statistics import NormalDist
    return m + NormalDist().inv_cdf(conf) * sd / n ** 0.5


def make_policies(cfg: Config | None = None):
    cfg = cfg or Config()
    full = dict(security=True, cost=True, regression=True, uncertainty=True, curated_evidence=True, fault_aware=True)
    pols = {
        "accuracy_only": Policy("accuracy_only", cfg=cfg),
        "hard_gates": Policy("hard_gates", security=True, cost=True, regression=True, cfg=cfg),
        "ravel": Policy("ravel", cfg=cfg, **full),
    }
    for comp in ("security", "cost", "regression", "uncertainty", "curated_evidence", "fault_aware"):
        kw = dict(full)
        kw[comp] = False
        pols[f"ravel_no_{comp}"] = Policy(f"ravel_no_{comp}", cfg=cfg, **kw)
    return pols
