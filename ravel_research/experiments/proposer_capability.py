"""Summarise the proposer-capability probes: 12 proposals each from the seed harness (clean report)."""
import json
import os
import sys

PROBES = {"proposer_probe_4b_rewrite": ("Qwen3.5-4B", "full rewrite"),
          "proposer_probe_4b_handler": ("Qwen3.5-4B", "handler"),
          "proposer_probe_9b_handler": ("Qwen3.5-9B", "handler")}


def summarise(d, n_props=12):
    cands = [json.loads(l) for l in open(os.path.join(d, "candidates.jsonl"))]
    evals = {json.loads(l)["cid"]: json.loads(l)["episodes"] for l in open(os.path.join(d, "evals.jsonl"))}
    seed = next(c["cid"] for c in cands if c["meta"].get("seed_harness"))
    s = evals[seed]
    acc = lambda e, p: sum(v["correct"] for k, v in e.items() if k.startswith(p))
    props = [c for c in cands if not c["meta"].get("seed_harness")]
    out = {"proposals": n_props, "no_code": n_props - len(props), "load_fail": 0, "runs": 0,
           "dev_up": 0, "test_up3": 0, "dev_up_test_down": 0}
    for c in props:
        e = evals[c["cid"]]
        if all((v["error"] or "").startswith("load_error") for v in e.values()):
            out["load_fail"] += 1
            continue
        out["runs"] += 1
        dg, tg = acc(e, "dev") - acc(s, "dev"), acc(e, "test") - acc(s, "test")
        out["dev_up"] += dg > 0
        out["test_up3"] += tg >= 3
        out["dev_up_test_down"] += dg > 0 and tg < 0
    return out


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "results"
    res = {k: {"model": m, "format": f, **summarise(os.path.join(root, k))} for k, (m, f) in PROBES.items()}
    json.dump(res, open(os.path.join(root, "proposer_capability.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))
