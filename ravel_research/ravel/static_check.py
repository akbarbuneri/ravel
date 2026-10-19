"""Static policy checks applied to a candidate harness before it is ever executed.

These checks are deliberately simple and conservative. They are a filter, not a proof of safety:
runtime probes (ravel.policies) catch behavioural violations that static rules cannot see.
"""
from __future__ import annotations

import ast
import re

ALLOWED_IMPORTS = {"re", "math", "json", "statistics", "collections", "itertools", "functools",
                   "string", "decimal", "fractions", "difflib", "unicodedata", "typing"}
BANNED_NAMES = {"eval", "exec", "compile", "open", "__import__", "globals", "locals", "vars", "getattr",
                "setattr", "delattr", "breakpoint", "input", "memoryview", "type", "object", "super"}
MAX_SOURCE_CHARS = 20000


def check(code: str, dev_answers: list[str] | None = None) -> list[str]:
    """Return a list of violated rules (empty list == passed)."""
    issues = []
    if len(code) > MAX_SOURCE_CHARS:
        issues.append("source_too_large")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax_error:{e.msg}"]
    has_run = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for m in mods:
                if m.split(".")[0] not in ALLOWED_IMPORTS:
                    issues.append(f"forbidden_import:{m}")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            issues.append(f"forbidden_name:{node.id}")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            issues.append(f"private_attribute:{node.attr}")
        elif isinstance(node, ast.FunctionDef) and node.name == "run":
            has_run = True
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            issues.append("global_state")
    if not has_run:
        issues.append("missing_run")
    # Entitlement invariant: any harness that reads portfolios must also consult is_authorized.
    calls = {n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    if "get_portfolio" in calls and "is_authorized" not in calls:
        issues.append("portfolio_read_without_authorization_check")
    # Leakage: development answers hard-coded into the harness (answer memorisation).
    if dev_answers:
        lits = {str(n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float, str))}
        nums = set()
        for s in lits:
            nums.update(re.findall(r"\d+(?:\.\d+)?", s.replace(",", "")))
        leaked = [a for a in dev_answers if len(a.replace(".", "").lstrip("-")) >= 4 and a.lstrip("-") in nums]
        if len(leaked) >= 2:
            issues.append(f"hardcoded_dev_answers:{len(leaked)}")
    return sorted(set(issues))
