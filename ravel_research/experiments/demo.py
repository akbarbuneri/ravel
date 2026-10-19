import json
from dataclasses import asdict
from ravel.core import Outcome, evaluate, wilson_upper

parent = Outcome('seed', 70, 100, 0, 100, 1500, 1200, True)
candidates = [
    Outcome('accurate_but_unsafe', 84, 100, 0, 100, 1500, 1200, False),
    Outcome('accurate_but_expensive', 88, 100, 0, 100, 7000, 3300, True),
    Outcome('accurate_but_regressive', 83, 100, 12, 100, 1800, 1350, True),
    Outcome('balanced_candidate', 78, 100, 0, 100, 2200, 1750, True),
]
print(json.dumps({'metadata': {'study': 'illustrative fixture only', 'real_llm_experiments': False},
'candidates': [dict(**asdict(c), accuracy=c.accuracy, wilson_regression_upper=wilson_upper(c.protected_regressions,c.protected_trials),
accuracy_only_accept=c.accuracy>parent.accuracy,
ravel_decision=evaluate(parent,c)) for c in candidates]}, indent=2))
