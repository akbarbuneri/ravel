"""RAVEL v0.1: deterministic acceptance-policy prototype, not an LLM harness."""
from dataclasses import dataclass, asdict
from math import sqrt
from statistics import NormalDist

@dataclass(frozen=True)
class Outcome:
    name: str
    successes: int
    trials: int
    protected_regressions: int
    protected_trials: int
    tokens: int
    latency_ms_p95: float
    security_checks_passed: bool
    edit_applies: bool = True

    @property
    def accuracy(self):
        return self.successes / self.trials if self.trials else 0.0

    @property
    def regression_rate(self):
        return self.protected_regressions / self.protected_trials if self.protected_trials else 1.0


def wilson_upper(errors: int, n: int, confidence: float = 0.95) -> float:
    """One-sided Wilson upper bound, not a formal deployment assurance."""
    if not n: return 1.0
    z = NormalDist().inv_cdf(confidence)
    p = errors / n
    return min(1.0, (p + z*z/(2*n) + z*sqrt((p*(1-p) + z*z/(4*n))/n))/(1+z*z/n))


def evaluate(parent: Outcome, candidate: Outcome, *, max_regression_upper=0.15,
             max_tokens=3000, max_p95_ms=2500, min_accuracy_gain=0.0):
    if not candidate.edit_applies: return False, 'invalid_edit'
    if not candidate.security_checks_passed: return False, 'security_gate'
    if candidate.tokens > max_tokens: return False, 'token_budget'
    if candidate.latency_ms_p95 > max_p95_ms: return False, 'latency_budget'
    if candidate.protected_trials == 0: return False, 'missing_regression_evidence'
    if wilson_upper(candidate.protected_regressions, candidate.protected_trials) > max_regression_upper:
        return False, 'regression_confidence_gate'
    if candidate.accuracy < parent.accuracy + min_accuracy_gain:
        return False, 'no_accuracy_gain'
    return True, 'accepted_on_measured_tests'
