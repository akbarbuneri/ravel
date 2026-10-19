"""Turn analysis.json into the paper's tables (LaTeX) and figures (PDF/PNG), plus a summary JSON."""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import binomtest  # noqa: E402

from experiments.analyze import boot_ci  # noqa: E402

# reference palette, slots 1-3 (validated all-pairs) + neutral for the seed baseline
COL = {"ravel": "#2a78d6", "accuracy_only": "#eb6834", "hard_gates": "#1baf7a", "seed": "#8c8b86"}
LABEL = {"seed": "Seed (no adaptation)", "accuracy_only": "Accuracy-only", "hard_gates": "Hard gates", "ravel": "RAVEL"}
COND_LABEL = {"clean": "Clean", "adversarial": "Adversarial proposer", "noisy": "Noisy feedback"}
POLICIES = ["seed", "accuracy_only", "hard_gates", "ravel"]
VARIANTS = ["accuracy_only", "hard_gates", "ravel", "ravel_no_security", "ravel_no_cost", "ravel_no_regression",
            "ravel_no_uncertainty", "ravel_no_curated_evidence", "ravel_no_fault_aware"]
VLABEL = {"accuracy_only": "Accuracy-only", "hard_gates": "Hard gates (point est.)", "ravel": "RAVEL (full)",
          "ravel_no_security": "-- security gate", "ravel_no_cost": "-- cost gate",
          "ravel_no_regression": "-- regression gate", "ravel_no_uncertainty": "-- uncertainty (point est.)",
          "ravel_no_curated_evidence": "-- curated evidence", "ravel_no_fault_aware": "-- fault awareness"}

plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#52514e", "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
                     "legend.frameon": False, "pdf.fonttype": 42})


def pct(x):
    return f"{100 * x:.1f}"


def fmt_ci(m, lo, hi, scale=100, d=1):
    return f"{m * scale:.{d}f} [{lo * scale:.{d}f}, {hi * scale:.{d}f}]"


def trajectory_table(traj, conds):
    rows = []
    summary = {}
    for c in conds:
        for p in POLICIES:
            rs = [r for r in traj if r["cond"] == c and r["policy"] == p]
            if not rs:
                continue
            seed_acc = {r["seed"]: r["test_acc"] for r in traj if r["cond"] == c and r["policy"] == "seed"}
            gains = [r["test_acc"] - seed_acc[r["seed"]] for r in rs]
            acc = boot_ci([r["test_acc"] for r in rs])
            g = boot_ci(gains)
            unsafe = sum(1 for r in rs if r["unauth_reads"] > 0 or r["exfil"])
            leak = sum(r["leak_accepted"] for r in rs)
            summary[f"{c}|{p}"] = {"test_acc": acc, "gain": g, "tokens": float(np.mean([r["tokens"] for r in rs])),
                                   "unsafe_final_runs": unsafe, "n": len(rs),
                                   "accepted": float(np.mean([r["accepted"] for r in rs])),
                                   "unsafe_accepted": sum(r["unsafe_accepted"] for r in rs), "leak_accepted": leak,
                                   "regression": float(np.mean([r["regression_vs_seed"] for r in rs])),
                                   "injected": float(np.mean([r["injected"] for r in rs])),
                                   "dev_minus_test": float(np.mean([r["dev_acc"] - r["test_acc"] for r in rs]))}
            s = summary[f"{c}|{p}"]
            rows.append(f"{COND_LABEL[c] if p == 'seed' else ''} & {LABEL[p]} & {fmt_ci(*acc)} & "
                        f"{g[0] * 100:+.1f} & {s['tokens']:.0f} & {s['accepted']:.1f} & "
                        f"{s['unsafe_accepted']} & {leak} & {unsafe}/{len(rs)} & {100 * s['regression']:.1f} \\\\")
        rows.append("\\midrule")
    rows = rows[:-1]
    tex = ("\\begin{tabular}{llrrrrrrrr}\n\\toprule\n"
           "Condition & Policy & Test acc.\\ (\\%) [95\\% CI] & $\\Delta$ seed & Tok/q & Acc.\\ edits & Unsafe acc. & Leak acc. & Unsafe final & Regr.\\ (\\%) \\\\\n\\midrule\n"
           + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    return tex, summary


def decision_table(dec):
    valid = [d for d in dec if d.get("valid")]
    cats = ["security", "injection", "leakage", "cost", "regression"]
    out = {}
    lines = []
    harmful = [d for d in valid if d["harms"]]
    benef = [d for d in valid if d["beneficial"]]
    neutral = [d for d in valid if not d["harms"] and not d["beneficial"]]
    for v in VARIANTS:
        rec = {}
        for cat in cats:
            xs = [d for d in valid if cat in d["harms"]]
            rec[cat] = (sum(d[f"pass_{v}"] for d in xs), len(xs))
        rec["any_harm"] = (sum(d[f"pass_{v}"] for d in harmful), len(harmful))
        rec["beneficial"] = (sum(d[f"pass_{v}"] for d in benef), len(benef))
        rec["neutral"] = (sum(d[f"pass_{v}"] for d in neutral), len(neutral))
        passed = [d for d in valid if d[f"pass_{v}"]]
        rec["precision"] = (sum(d["beneficial"] for d in passed), len(passed))
        rec["mean_test_gain_passed"] = float(np.mean([d["test_gain"] for d in passed])) if passed else float("nan")
        out[v] = rec

        def f(t):
            k, n = t
            return f"{k}/{n}" if n else "--"
        lines.append(f"{VLABEL[v]} & " + " & ".join(f(rec[c]) for c in cats) + f" & {f(rec['any_harm'])} & "
                     f"{f(rec['beneficial'])} & {f(rec['neutral'])} & {f(rec['precision'])} & "
                     f"{100 * rec['mean_test_gain_passed']:+.1f} \\\\")
        if v == "ravel":
            lines.append("\\midrule")
    tex = ("\\begin{tabular}{lrrrrrrrrrr}\n\\toprule\n"
           "& \\multicolumn{6}{c}{Harmful candidates passed} & & & & \\\\\n\\cmidrule(lr){2-7}\n"
           "Acceptance gates & Secur. & Inject. & Leak & Cost & Regr. & Any & Benef.\\ passed & Neutral passed & Precision & $\\overline{\\Delta}$test (pp) \\\\\n\\midrule\n"
           + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")
    counts = {"valid": len(valid), "invalid": len(dec) - len(valid), "harmful": len(harmful),
              "beneficial": len(benef), "neutral": len(neutral),
              "by_harm": {c: sum(1 for d in valid if c in d["harms"]) for c in cats}}
    return tex, out, counts


def fig_curves(traj, conds, path):
    fig, axes = plt.subplots(1, len(conds), figsize=(7.0, 2.3), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, c in zip(axes, conds):
        for p in POLICIES:
            rs = [r for r in traj if r["cond"] == c and r["policy"] == p]
            if not rs:
                continue
            m = np.array([r["curve"] for r in rs]) * 100
            x = np.arange(m.shape[1])
            mu = m.mean(0)
            ax.plot(x, mu, color=COL[p], lw=2 if p != "seed" else 1.2, ls="-" if p != "seed" else "--",
                    marker="o" if p != "seed" else None, ms=3.5, label=LABEL[p], zorder=3 if p == "ravel" else 2)
            if len(rs) > 1 and p != "seed":
                ax.fill_between(x, m.min(0), m.max(0), color=COL[p], alpha=0.10, lw=0)
        ax.set_title(COND_LABEL[c], fontsize=9)
        ax.set_xlabel("Revision round")
        ax.set_xticks(range(m.shape[1]))
    axes[0].set_ylabel("Held-out test accuracy (%)")
    axes[-1].legend(loc="lower right", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(path + ".pdf")
    fig.savefig(path + ".png", dpi=200)
    plt.close(fig)


def fig_gates(dstats, path):
    vs = VARIANTS
    harm = [dstats[v]["any_harm"] for v in vs]
    ben = [dstats[v]["beneficial"] for v in vs]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
    y = np.arange(len(vs))[::-1]
    for ax, data, title, col in ((axes[0], harm, "Harmful candidates passed (%)", "#e34948"),
                                 (axes[1], ben, "Beneficial candidates passed (%)", "#2a78d6")):
        vals = [100 * k / n if n else 0 for k, n in data]
        ax.barh(y, vals, color=col, height=0.62, edgecolor="white", linewidth=1)
        for yi, (k, n), v in zip(y, data, vals):
            ax.text(v + 1.5, yi, f"{k}/{n}", va="center", fontsize=7, color="#52514e")
        ax.set_title(title, fontsize=9)
        ax.set_xlim(0, 112)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([VLABEL[v] for v in vs])
    fig.tight_layout()
    fig.savefig(path + ".pdf")
    fig.savefig(path + ".png", dpi=200)
    plt.close(fig)


def fig_devtest(dec, path):
    valid = [d for d in dec if d.get("valid")]
    fig, ax = plt.subplots(figsize=(3.4, 2.8))
    rng = np.random.default_rng(0)
    groups = [("Rejected by RAVEL", [d for d in valid if not d["pass_ravel"]], "#c3c2b7", 10),
              ("Passed by RAVEL", [d for d in valid if d["pass_ravel"]], COL["ravel"], 22)]
    for name, ds, col, s in groups:
        x = np.array([d["dev_gain"] for d in ds]) * 100 + rng.normal(0, 0.35, len(ds))
        yv = np.array([d["test_gain"] for d in ds]) * 100 + rng.normal(0, 0.35, len(ds))
        ax.scatter(x, yv, s=s, color=col, edgecolor="white", linewidth=0.6, label=name, zorder=3 if "Passed" in name else 2)
    leak = [d for d in valid if "leakage" in d["harms"]]
    if leak:
        ax.scatter([d["dev_gain"] * 100 for d in leak], [d["test_gain"] * 100 for d in leak], s=30, facecolor="none",
                   edgecolor="#eb6834", linewidth=1.2, label="Answer-leak mutation", zorder=4)
    ax.axhline(0, color="#52514e", lw=0.8)
    ax.axvline(0, color="#52514e", lw=0.8)
    ax.set_xlabel("Development gain over parent (pp)")
    ax.set_ylabel("Held-out test gain over parent (pp)")
    ax.legend(fontsize=6.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(path + ".pdf")
    fig.savefig(path + ".png", dpi=200)
    plt.close(fig)


def paired_tests(traj, conds):
    """Per unit, compare final test accuracy of RAVEL vs other policies (exact sign test over non-ties)."""
    res = {}
    for other in ["accuracy_only", "hard_gates", "seed"]:
        diffs = []
        for c in conds:
            a = {r["seed"]: r["test_acc"] for r in traj if r["cond"] == c and r["policy"] == "ravel"}
            b = {r["seed"]: r["test_acc"] for r in traj if r["cond"] == c and r["policy"] == other}
            diffs += [a[s] - b[s] for s in a if s in b]
        wins, losses = sum(d > 1e-9 for d in diffs), sum(d < -1e-9 for d in diffs)
        p = binomtest(wins, wins + losses, 0.5).pvalue if wins + losses else 1.0
        res[other] = {"mean_diff": float(np.mean(diffs)) if diffs else float("nan"),
                      "ci": boot_ci(diffs)[1:], "wins": wins, "losses": losses, "ties": len(diffs) - wins - losses,
                      "sign_test_p": p}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", default="results/study")
    ap.add_argument("--out", default="paper/generated")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    d = json.load(open(os.path.join(a.study, "analysis.json")))
    traj, dec = d["trajectories"], d["decisions"]
    conds = [c for c in ["clean", "adversarial", "noisy"] if any(r["cond"] == c for r in traj)]
    t1, s1 = trajectory_table(traj, conds)
    open(os.path.join(a.out, "tab_trajectories.tex"), "w").write(t1)
    t2, s2, counts = decision_table(dec)
    open(os.path.join(a.out, "tab_decisions.tex"), "w").write(t2)
    fig_curves(traj, conds, os.path.join(a.out, "fig_curves"))
    fig_gates(s2, os.path.join(a.out, "fig_gates"))
    fig_devtest(dec, os.path.join(a.out, "fig_devtest"))
    tests = paired_tests(traj, conds)
    # rejection reasons of RAVEL on valid candidates
    why = defaultdict(int)
    for x in dec:
        if x.get("valid"):
            why[x["why_ravel"]] += 1
    summary = {"trajectories": s1, "decisions": s2, "counts": counts, "paired_vs_ravel": tests,
               "ravel_reasons": dict(why),
               "dev_test_corr": float(np.corrcoef([x["dev_gain"] for x in dec if x.get("valid")],
                                                  [x["test_gain"] for x in dec if x.get("valid")])[0, 1])}
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1, default=str)
    print(json.dumps({"counts": counts, "paired": tests, "ravel_reasons": dict(why)}, indent=1, default=str))


if __name__ == "__main__":
    main()
