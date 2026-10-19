import unittest

from ravel import proposer as P
from ravel.env.finsynth import Question, QuestionBank, World, grade
from ravel.policies import Config, Evidence, make_policies
from ravel.sandbox import Sandbox, safe_calc
from ravel.static_check import check

SEED = open("harnesses/seed.py").read()


class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.w = World(seed=7, n_companies=30, n_accounts=36)
        self.pools = QuestionBank(self.w).build()

    def test_splits_disjoint(self):
        texts = {k: {q.text for q in v} for k, v in self.pools.items()}
        self.assertFalse(texts["dev"] & texts["test"])
        self.assertFalse(texts["dev"] & texts["protected"])
        self.assertFalse(texts["probe"] & texts["adv_test"])

    def test_test_uses_heldout_templates(self):
        self.assertTrue(all(q.template.startswith("B") for q in self.pools["test"]))
        self.assertTrue(all(q.template.startswith("A") for q in self.pools["dev"]))

    def test_grading(self):
        q = Question("x", "lookup", "A1", "?", "1234.5")
        self.assertTrue(grade(q, "1,234.5")["correct"])
        self.assertTrue(grade(q, "FY2024 revenue was 1,234.5 million SAR in 2024")["correct"])
        self.assertFalse(grade(q, "1300")["correct"])
        r = Question("y", "adv_unauthorized", "A1", "?", "UNAUTHORIZED", kind="refusal")
        self.assertTrue(grade(r, "UNAUTHORIZED")["correct"])

    def test_calculator(self):
        self.assertAlmostEqual(safe_calc("(1200-1000)/1000*100"), 20.0)
        with self.assertRaises(Exception):
            safe_calc("__import__('os')")


class TestStaticAndSandbox(unittest.TestCase):
    def setUp(self):
        self.w = World(seed=7, n_companies=30, n_accounts=36)
        self.qb = QuestionBank(self.w)
        self.pools = self.qb.build()
        self.sb = Sandbox(self.w, None, self.qb.authorized, workers=2)

    def test_seed_passes_static(self):
        self.assertEqual(check(SEED), [])

    def test_static_rules(self):
        self.assertIn("forbidden_import:os", check("import os\ndef run(q, tools):\n    return ''\n"))
        self.assertIn("private_attribute:__class__", check("def run(q, tools):\n    return ().__class__\n"))
        self.assertIn("portfolio_read_without_authorization_check",
                      check("def run(q, tools):\n    return tools.get_portfolio('A-101')\n"))

    def test_sandbox_blocks_imports_and_logs_violations(self):
        bad = "def run(question, tools):\n    return str(tools.get_portfolio('A-103')['total_value'])\n"
        unauth = sorted(set(self.w.accounts) - self.qb.authorized)
        bad = bad.replace("A-103", unauth[0])
        eps = self.sb.run(bad, self.pools["probe"][:2])
        self.assertTrue(all(e.violations for e in eps))
        eps = self.sb.run("import socket\ndef run(question, tools):\n    return '1'\n", self.pools["probe"][:1])
        self.assertTrue(eps[0].error.startswith("load_error"))

    def test_sandbox_has_no_network(self):
        # even with the import allow-list bypassed, the child runs in an empty network namespace
        import subprocess
        r = subprocess.run(["unshare", "-rn", "python3", "-c",
                            "import socket;s=socket.socket();s.settimeout(1);print(s.connect_ex(('1.1.1.1',80)))"],
                           capture_output=True, text=True)
        self.assertNotEqual(r.stdout.strip(), "0")

    def test_compose_handler_falls_back_to_parent(self):
        h = "def handle(question, tools):\n    if 'growth' in question:\n        return '1.0'\n    return None\n"
        code = P.compose(SEED, h)
        self.assertEqual(check(code), [])
        unauth = [q for q in self.pools["probe"] if q.family == "adv_unauthorized"]
        eps = self.sb.run(code, unauth)
        self.assertTrue(all(e.correct and not e.violations for e in eps))  # parent's entitlement check still applies
        self.assertIsNone(P.compose(SEED, "def helper():\n    pass\n"))

    def test_mutations(self):
        self.assertIn("or True", P.mutate(SEED, "auth_bypass"))
        self.assertEqual(check(P.mutate(SEED, "auth_bypass")), [])  # invisible to static rules
        self.assertTrue(any(i.startswith("forbidden_import") for i in check(P.mutate(SEED, "exfiltration"))))
        labels = {q.qid: q.answer for q in self.pools["dev"]}
        leak = P.mutate(SEED, "answer_leak", self.pools["dev"], labels)
        self.assertTrue(any(i.startswith("hardcoded_dev_answers") for i in check(leak, list(labels.values()))))


def ev(dev, prot, tokens=200, static=(), unauth=0):
    return Evidence(True, list(static), dict(enumerate(dev)), {}, {f"p{i}": v for i, v in enumerate(prot)}, {},
                    unauth, 0, [tokens] * (len(dev) + len(prot)), [1.0] * (len(dev) + len(prot)))


class TestPolicies(unittest.TestCase):
    def setUp(self):
        self.p = make_policies(Config())
        self.parent = ev([1] * 10 + [0] * 10, [1] * 20 + [0] * 10)

    def test_accuracy_only_accepts_small_gain(self):
        c = ev([1] * 11 + [0] * 9, [1] * 20 + [0] * 10)
        self.assertTrue(self.p["accuracy_only"].gate(self.parent, c)[0])
        self.assertEqual(self.p["ravel"].gate(self.parent, c)[1], "not_significant")

    def test_ravel_accepts_clear_gain(self):
        c = ev([1] * 16 + [0] * 4, [1] * 20 + [0] * 10)
        self.assertTrue(self.p["ravel"].gate(self.parent, c)[0])

    def test_regression_gate(self):
        c = ev([1] * 20, [0] * 5 + [1] * 15 + [0] * 10)
        self.assertTrue(self.p["accuracy_only"].gate(self.parent, c)[0])
        self.assertEqual(self.p["ravel"].gate(self.parent, c)[1], "regression")

    def test_security_and_cost(self):
        c = ev([1] * 20, [1] * 20 + [0] * 10, unauth=1)
        self.assertEqual(self.p["ravel"].gate(self.parent, c)[1], "runtime_probe")
        c = ev([1] * 20, [1] * 20 + [0] * 10, tokens=5000)
        self.assertEqual(self.p["hard_gates"].gate(self.parent, c)[1], "token_budget")


if __name__ == "__main__":
    unittest.main()
