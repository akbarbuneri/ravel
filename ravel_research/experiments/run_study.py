"""Main RAVEL study: multi-round harness adaptation under three conditions and several selection policies.

All policies within a (condition, seed) unit receive identical proposals for identical parents
(common random numbers via the deterministic LLM cache) and identical evaluations, so the optimization
budget is matched by construction. Units are advanced in lockstep, one round at a time, which keeps
GPU model swaps between the proposer and the solver to two per round.

Usage:  python -m experiments.run_study --seeds 0 1 2 3 --rounds 5 --k 4
Re-running is cheap: proposals, solver calls and evaluations are all cached.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace

from ravel import proposer as P
from ravel.env.finsynth import QuestionBank, World, _fmt, _h, grade
from ravel.llm import LLM
from ravel.policies import Config, Evidence, make_policies
from ravel.sandbox import Sandbox
from ravel.static_check import check

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONDITIONS = {
    "clean": dict(label_noise=0.0, fault_rate=0.0, adversarial=0.0),
    "adversarial": dict(label_noise=0.0, fault_rate=0.0, adversarial=0.3),
    "noisy": dict(label_noise=0.2, fault_rate=0.3, adversarial=0.0),
}
MAIN_POLICIES = ["accuracy_only", "hard_gates", "ravel"]
SPLITS = ["dev", "protected", "probe", "test", "adv_test"]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


class Study:
    def __init__(self, out_dir, proposer_model, solver_model, workers=4, eval_par=3, prop_par=4):
        self.out = out_dir
        os.makedirs(out_dir, exist_ok=True)
        self.world = World(seed=7, n_companies=30, n_accounts=36)
        self.qb = QuestionBank(self.world)
        self.pools = self.qb.build()
        self.qmap = {q.qid: q for qs in self.pools.values() for q in qs}
        cache = os.path.join(ROOT, "results", "llm_cache.sqlite")
        self.solver = LLM(solver_model, cache, num_ctx=8192, max_concurrent=4)
        self.prop_llm = LLM(proposer_model, cache, num_ctx=8192)
        self.sandbox = Sandbox(self.world, self.solver, self.qb.authorized, workers=workers)
        self.eval_par, self.prop_par = eval_par, prop_par
        self.lock = threading.Lock()
        self.codes = {}  # cid -> code
        self.cand_meta = {}  # cid -> provenance
        self.evals = {}  # (cid, fault_rate) -> {qid: episode dict}
        self._load()

    # ------------------------------------------------------------------ persistence
    def _load(self):
        p = os.path.join(self.out, "evals.jsonl")
        if os.path.exists(p):
            for line in open(p):
                r = json.loads(line)
                self.evals[(r["cid"], r["fault_rate"])] = r["episodes"]
        p = os.path.join(self.out, "candidates.jsonl")
        if os.path.exists(p):
            for line in open(p):
                r = json.loads(line)
                self.codes[r["cid"]] = r["code"]
                self.cand_meta.setdefault(r["cid"], []).append(r["meta"])

    def _append(self, name, row):
        with self.lock, open(os.path.join(self.out, name), "a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def register(self, code, meta):
        cid = sha(code)
        with self.lock:
            new = cid not in self.codes
            self.codes[cid] = code
            known = meta in self.cand_meta.get(cid, [])
            self.cand_meta.setdefault(cid, []).append(meta)
        if new or not known:
            self._append("candidates.jsonl", {"cid": cid, "code": code, "meta": meta})
        return cid

    # ------------------------------------------------------------------ evaluation
    def evaluate(self, cid, fault_rate):
        key = (cid, fault_rate)
        if key in self.evals:
            return self.evals[key]
        qs = [q for s in SPLITS for q in self.pools[s]]
        eps = self.sandbox.run(self.codes[cid], qs, fault_rate=fault_rate, fault_seed=1)
        out = {}
        for q, e in zip(qs, eps):
            d = asdict(e)
            d["trace"] = [list(map(lambda x: str(x)[:90], t)) for t in d["trace"][:6]] if q.qid.startswith("dev") else []
            d["answer"] = d["answer"][:160]
            out[q.qid] = d
        with self.lock:
            self.evals[key] = out
        self._append("evals.jsonl", {"cid": cid, "fault_rate": fault_rate, "episodes": out})
        return out

    # ------------------------------------------------------------------ labels & evidence
    def noisy_labels(self, cond, seed):
        cfg = CONDITIONS[cond]
        labels = {}
        for q in self.pools["dev"]:
            lab = q.answer
            if cfg["label_noise"] and _h("noise", seed, q.qid) < cfg["label_noise"] and q.kind == "numeric":
                f = 1 + random.Random(f"{seed}{q.qid}").choice([-1, 1]) * random.Random(f"m{seed}{q.qid}").uniform(0.15, 0.4)
                lab = _fmt(round(float(q.answer) * f, 1))
            labels[q.qid] = lab
        return labels

    def evidence(self, cid, cond, labels):
        fr = CONDITIONS[cond]["fault_rate"]
        if cid is None or cid not in self.codes:
            return Evidence(False, ["no_code"], {}, {}, {}, {}, 0, 0, [], [])
        ev = self.evaluate(cid, fr)
        loads = not all((e["error"] or "").startswith("load_error") for e in ev.values())
        dev_c, dev_f, pc, pf = {}, {}, {}, {}
        toks, lats = [], []
        for q in self.pools["dev"]:
            e = ev[q.qid]
            dev_c[q.qid] = grade(replace(q, answer=labels[q.qid]), e["answer"])["correct"]
            dev_f[q.qid] = e["faults"] > 0
            toks.append(e["tokens"]); lats.append(e["latency_s"])
        for q in self.pools["protected"]:
            e = ev[q.qid]
            pc[q.qid], pf[q.qid] = e["correct"], e["faults"] > 0
            toks.append(e["tokens"]); lats.append(e["latency_s"])
        probe = [ev[q.qid] for q in self.pools["probe"]]
        static = check(self.codes[cid], dev_answers=list(labels.values()))
        return Evidence(loads, static, dev_c, dev_f, pc, pf,
                        sum(1 for e in probe if e["violations"]), sum(1 for e in probe if e["injected"]), toks, lats)

    def dev_episodes(self, cid, cond):
        from ravel.sandbox import Episode
        ev = self.evaluate(cid, CONDITIONS[cond]["fault_rate"])
        return [Episode(**{**ev[q.qid], "trace": [tuple(t) for t in ev[q.qid]["trace"]]}) for q in self.pools["dev"]]

    # ------------------------------------------------------------------ proposals
    def proposals(self, cond, seed, rnd, parent, labels, k):
        """K candidate ids for (unit, round, parent). Deterministic given the inputs."""
        eps = self.dev_episodes(parent, cond)
        # re-grade with the labels the optimizer sees
        for q, e in zip(self.pools["dev"], eps):
            e.correct = grade(replace(q, answer=labels[q.qid]), e.answer)["correct"]
        report = P.build_report(self.pools["dev"], eps, labels=labels, fault_aware=True,
                                rng=random.Random(f"report-{seed}-{rnd}"))
        def gen(j):
            d = int(_h("dir", seed, rnd, j) * len(P.DIRECTIVES))
            return (d,) + P.propose(self.prop_llm, self.codes[parent], report, P.DIRECTIVES[d],
                                    seed=int(_h("pseed", seed, rnd, j) * 2 ** 31))

        with ThreadPoolExecutor(k) as ex:
            raw = list(ex.map(gen, range(k)))
        out = []
        for j, (directive_i, code, r) in enumerate(raw):
            meta = {"cond": cond, "seed": seed, "round": rnd, "k": j, "parent": parent,
                    "directive": directive_i, "mutation": None, "proposal_tokens": r["completion_tokens"]}
            if code is None:
                out.append(None)
                continue
            if CONDITIONS[cond]["adversarial"] and _h("mut", seed, rnd, j) < CONDITIONS[cond]["adversarial"]:
                kind = P.MUTATIONS[int(_h("kind", seed, rnd, j) * len(P.MUTATIONS))]
                m = P.mutate(code, kind, self.pools["dev"], labels)
                if m is not None:
                    code, meta["mutation"] = m, kind
            out.append(self.register(code, meta))
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    ap.add_argument("--policies", nargs="+", default=MAIN_POLICIES)
    ap.add_argument("--proposer", default="qwen35-faster:latest")
    ap.add_argument("--solver", default="qwen3.5:4b")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "study"))
    a = ap.parse_args()

    st = Study(a.out, a.proposer, a.solver)
    pols = make_policies(Config())
    seed_cid = st.register(open(os.path.join(ROOT, "harnesses", "seed.py")).read(), {"seed_harness": True})
    units = [(c, s) for c in a.conditions for s in a.seeds]
    labels = {u: st.noisy_labels(*u) for u in units}
    state = {(c, s, p): seed_cid for c, s in units for p in a.policies}
    log_path = os.path.join(a.out, "rounds.jsonl")
    done = set()
    if os.path.exists(log_path):
        for line in open(log_path):
            r = json.loads(line)
            done.add((r["cond"], r["seed"], r["policy"], r["round"]))
    t_start = time.time()
    for rnd in range(1, a.rounds + 1):
        t0 = time.time()
        # Phase 0: make sure every parent is evaluated (solver loaded)
        for c in {c for c, _ in units}:
            for cid in {v for (cc, _, _), v in state.items() if cc == c}:
                st.evaluate(cid, CONDITIONS[c]["fault_rate"])
        # Phase 1: proposals for every distinct (unit, parent) (proposer loaded)
        jobs = sorted({(c, s, state[(c, s, p)]) for c, s in units for p in a.policies})
        with ThreadPoolExecutor(st.prop_par) as ex:
            props = dict(zip(jobs, ex.map(lambda j: st.proposals(j[0], j[1], rnd, j[2], labels[(j[0], j[1])], a.k), jobs)))
        t1 = time.time()
        # Phase 2: evaluate all new candidates (solver loaded)
        need = sorted({(cid, CONDITIONS[c]["fault_rate"]) for (c, s, _), cids in props.items() for cid in cids if cid})
        with ThreadPoolExecutor(st.eval_par) as ex:
            list(ex.map(lambda x: st.evaluate(*x), need))
        t2 = time.time()
        # Phase 3: selection
        for c, s in units:
            for p in a.policies:
                parent = state[(c, s, p)]
                cids = props[(c, s, parent)]
                pe = st.evidence(parent, c, labels[(c, s)])
                ces = [st.evidence(cid, c, labels[(c, s)]) for cid in cids]
                best, decs = pols[p].select(pe, ces)
                new = cids[best] if best is not None else parent
                if (c, s, p, rnd) not in done:
                    st._append("rounds.jsonl", {"cond": c, "seed": s, "policy": p, "round": rnd, "parent": parent,
                                                "candidates": cids, "decisions": [d[1] for d in decs], "accepted": new if best is not None else None})
                state[(c, s, p)] = new
        print(f"[round {rnd}] jobs={len(jobs)} new_evals={len(need)} propose={t1 - t0:.0f}s eval={t2 - t1:.0f}s "
              f"total={time.time() - t_start:.0f}s solver_live={st.solver.live_calls}", flush=True)
    json.dump({"final": {f"{c}|{s}|{p}": v for (c, s, p), v in state.items()}, "args": vars(a)},
              open(os.path.join(a.out, "final_state.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
