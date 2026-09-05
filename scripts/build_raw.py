"""Generate data/final/raw/task{1-5}.jsonl — the structured source-of-truth for evaluation.
Each item is a normalised envelope tagged with `primary_category` (the per-task primary class
used to stratify model performance). CDRs are pre-computed (abnumber IMGT) so render_prompts.py
stays pure templating. Run once (or whenever the upstream task data changes). Env: epi_bench.
"""
import os, json, random, importlib.util, warnings
from collections import Counter
warnings.filterwarnings("ignore")

BALANCE_SEED = 20260630

ROOT = "/data/node2/home/zirui/benchmark/epitope/epitope_benchmark"
DATA = f"{ROOT}/data"
OUT = f"{ROOT}/data/final/raw"
os.makedirs(OUT, exist_ok=True)

_t = importlib.util.spec_from_file_location("tax", f"{ROOT}/scripts/34_taxonomy.py")
tax = importlib.util.module_from_spec(_t); _t.loader.exec_module(tax)


def cdrs(seq, scheme="imgt"):
    if not seq:
        return ["", "", ""]
    try:
        from abnumber import Chain
        c = Chain(seq, scheme=scheme)
        return [c.cdr1_seq, c.cdr2_seq, c.cdr3_seq]
    except Exception:
        return ["", "", ""]


def aseq(a):
    return a["seq"] if isinstance(a, dict) else a


def write(task, items):
    with open(f"{OUT}/{task}.jsonl", "w") as fh:
        for it in items:
            fh.write(json.dumps(it) + "\n")
    print(f"{task}: {len(items)}  primary_category dist: "
          f"{Counter(it['primary_category'] for it in items).most_common()}")


def balance_mcq(items, seed=BALANCE_SEED):
    """Permute each item's 4 options so the gold answer is as uniform as possible across
    A/B/C/D (removes any answer-position prior so a model can't exploit a label shortcut).
    Deterministic (seeded). Mutates label['answer'] and input['options'] in place."""
    rng = random.Random(seed)
    n = len(items)
    base, rem = divmod(n, 4)
    targets = [L for i, L in enumerate("ABCD") for _ in range(base + (1 if i < rem else 0))]
    rng.shuffle(targets)
    for it, tgt in zip(items, targets):
        opts = it["input"]["options"]
        gi = "ABCD".index(it["label"]["answer"])
        gold = opts[gi]
        others = [o for j, o in enumerate(opts) if j != gi]
        rng.shuffle(others)
        ti = "ABCD".index(tgt)
        it["input"]["options"] = others[:ti] + [gold] + others[ti:]
        it["label"]["answer"] = tgt
    print(f"  balanced MCQ answers -> {dict(sorted(Counter(it['label']['answer'] for it in items).items()))}")
    return items


# ---------------- Task1 — antigen-only union epitope (primary = targetable-region count) ----
def build_task1():
    patches = {x["id"]: x.get("patches") for x in (json.loads(l) for l in open(f"{DATA}/subtask2_rendered.jsonl"))}
    out = []
    for r in (json.loads(l) for l in open(f"{DATA}/subtask2.jsonl")):
        pat = patches.get(r["id"]) or []
        npat = len(pat)
        cat = "1 site" if npat == 1 else ("2 sites" if npat == 2 else "≥3 sites")
        out.append({"id": r["id"], "task": "task1", "primary_category": cat,
                    "input": {"antigen": aseq(r["antigen"])},
                    "label": {"union_epitope_positions": r["label"]["union_epitope_positions"], "patches": pat},
                    "meta": r.get("meta", {})})
    write("task1", out)


# ---------------- Task2 — antibody-conditioned epitope MCQ (primary = antigen taxon) ----------
def build_task2():
    out = []
    for r in (json.loads(l) for l in open(f"{DATA}/task123/task2_mcq.jsonl")):
        cat = tax.category(r.get("species", ""), r.get("pdb_id"))
        ab = r["antibody"]
        out.append({"id": r["id"], "task": "task2", "primary_category": cat,
                    "input": {"antibody": {"H": ab["H"], "L": ab["L"],
                                           "cdr_h": cdrs(ab["H"]), "cdr_l": cdrs(ab["L"])},
                              "antigen": aseq(r["antigen"]), "options": r["options"]},
                    "label": {"answer": r["label"]["answer"], "tier": r.get("tier")},
                    "meta": {"tier": r.get("tier"), "species": r.get("species", ""),
                             "pdb_id": r.get("pdb_id", ""), "source": r.get("source", "")}})
    balance_mcq(out)                              # uniform gold across A/B/C/D (no answer-position prior)
    write("task2", out)


# ---------------- Task3 — epitope binning (primary = difficulty tier) ------------------------
def build_task3():
    rows = [json.loads(l) for l in open(f"{DATA}/subtask3_binning.jsonl")]
    L = sorted(aseq(r["antigen"]).__len__() for r in rows)
    q1, q2 = L[len(L)//3], L[2*len(L)//3]
    out = []
    for r in rows:
        n = len(aseq(r["antigen"]))
        cat = "easy" if n <= q1 else ("medium" if n <= q2 else "hard")
        def ab(x):
            H = x["H"]["seq"] if isinstance(x["H"], dict) else x["H"]
            Lc = x["L"]["seq"] if isinstance(x["L"], dict) else x["L"]
            return {"H": H, "L": Lc, "cdr_h": cdrs(H), "cdr_l": cdrs(Lc)}
        lab = r["label"]["answer"] if isinstance(r["label"], dict) else r["label"]
        out.append({"id": r["id"], "task": "task3", "primary_category": cat,
                    "input": {"antigen": aseq(r["antigen"]),
                              "antibody_A": ab(r["antibody_A"]), "antibody_B": ab(r["antibody_B"])},
                    "label": {"answer": lab},
                    "meta": {**r.get("meta", {}), "antigen_len": n}})
    write("task3", out)


# ---------------- Task4 — functional-epitope MCQ (primary = mechanism) -----------------------
def build_task4():
    out = []
    for r in (json.loads(l) for l in open(f"{DATA}/task4_mcq.jsonl")):
        out.append({"id": r["id"], "task": "task4", "primary_category": r["meta"]["mechanism"],
                    "input": {"antigen": aseq(r["antigen"]), "options": r["options"],
                              "question_function": r.get("question_function", "")},
                    "label": {"answer": r["answer"]},
                    "meta": r.get("meta", {})})
    write("task4", out)


# ---------------- Task5 — antibody escape (primary = mutation residue class) -----------------
def build_task5():
    out = []
    for r in (json.loads(l) for l in open(f"{DATA}/task5.jsonl")):
        ab = r["antibody"]
        lo, hi = r["antigen_region"]
        out.append({"id": r["id"], "task": "task5", "primary_category": r["meta"]["mutation_type"],
                    "input": {"antibody": {"H": ab["H"], "L": ab["L"], "cdr_h": ab["cdrH"], "cdr_l": ab["cdrL"]},
                              "antigen": aseq(r["antigen"]), "antigen_region": [lo, hi], "mutation": r["mutation"]},
                    "label": {"answer": r["label"]},
                    "meta": {k: v for k, v in r["meta"].items() if k != "antibody_name"}})
    write("task5", out)


if __name__ == "__main__":
    build_task1(); build_task2(); build_task3(); build_task4(); build_task5()
    print("-> data/final/raw/")
