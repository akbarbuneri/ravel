# RAVEL Research — Initial Reproducibility Scaffold

**Status:** v0.1, methodological prototype. **No original LLM experiments have been run.** The demo uses fabricated, explicitly labeled test fixtures to validate acceptance policy behavior. It does not demonstrate a research finding or security guarantee.

## Run (Python >= 3.10, standard library only)

```bash
python -m unittest discover -s tests -v
python -m experiments.demo
```

For environments that do not resolve namespace packages, use `PYTHONPATH=.` from repo root.

## Contains
- `ravel/core.py`: outcome schema; one-sided Wilson regression bound; basic hard-constraint acceptance policy
- `experiments/demo.py`: four illustrative candidate outcomes, compares accuracy-only and gated decisions
- `tests/test_core.py`: deterministic tests for major gates
- `configs/pilot.json`: provisional experimental thresholds
- `RESEARCH_SPEC.md`: scientific protocol, benchmark, baselines, ablations, acceptance criteria
- `paper/OUTLINE.md`: planned manuscript, with no fabricated results

## Security limitation
`security_checks_passed` is a **mock external verdict**. No sandbox, secure code execution, static analyzer, or attack harness is implemented. Do not run untrusted generated code outside a properly isolated environment.
