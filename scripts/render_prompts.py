"""Render EpiBench evaluation prompts: read structured raw data (data/final/raw/) + editable
prompt templates (data/final/prompts/) and write the complete data/final/rendered_data.jsonl.

Re-run after editing any prompt template to re-sync rendered_data.jsonl. The templates hold the
editable PROSE + {placeholders}; this script fills the computed blocks (position-numbered
sequence, option lists, re-indexed mutation). Each rendered line:
  {id, task, primary_category, system, user, label, meta}
so eval can stratify each model's accuracy per task x primary_category.   Env: any python3.
"""
import os, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = f"{HERE}/raw"
TASKS = ["task1", "task2", "task3", "task4", "task5"]


def numbered(seq, start=1, width=10):
    return "\n".join(f"{start + i:>5} {seq[i:i + width]}" for i in range(0, len(seq), width))


def load_template(task, prompts_dir):
    txt = open(f"{prompts_dir}/{task}.txt").read()
    sysmark, usermark = "=== SYSTEM ===", "=== USER ==="
    sys = txt.split(sysmark, 1)[1].split(usermark, 1)[0].strip()
    user = txt.split(usermark, 1)[1].strip()
    return sys, user


# -------- per-task placeholder computation --------
def vals_task1(it):
    seq = it["input"]["antigen"]
    return {"antigen_len": len(seq), "numbered_antigen": numbered(seq)}


def vals_task2(it):
    seq = it["input"]["antigen"]; ab = it["input"]["antibody"]
    opts = []
    for li, o in enumerate(it["input"]["options"]):
        opts.append(f"{'ABCD'[li]}) " + ", ".join(f"{seq[p - 1]}{p}" for p in o))
    return {"vh": ab["H"], "cdr_h1": ab["cdr_h"][0], "cdr_h2": ab["cdr_h"][1], "cdr_h3": ab["cdr_h"][2],
            "vl": ab["L"], "cdr_l1": ab["cdr_l"][0], "cdr_l2": ab["cdr_l"][1], "cdr_l3": ab["cdr_l"][2],
            "antigen_len": len(seq), "numbered_antigen": numbered(seq), "options": "\n".join(opts)}


def vals_task3(it):
    seq = it["input"]["antigen"]; A = it["input"]["antibody_A"]; B = it["input"]["antibody_B"]
    v = {"antigen_len": len(seq), "numbered_antigen": numbered(seq)}
    for tag, ab in (("a", A), ("b", B)):
        v[f"{tag}_vh"] = ab["H"]; v[f"{tag}_vl"] = ab["L"]
        for i in (1, 2, 3):
            v[f"{tag}_cdr_h{i}"] = ab["cdr_h"][i - 1] or "-"
            v[f"{tag}_cdr_l{i}"] = ab["cdr_l"][i - 1] or "-"
    return v


def vals_task4(it):
    seq = it["input"]["antigen"]; opt = it["input"]["options"]
    lines = "\n".join(f"{L}. residues {opt[L]['start']}-{opt[L]['end']}: {opt[L]['seq']}" for L in ["A", "B", "C", "D"])
    return {"antigen_len": len(seq), "numbered_antigen": numbered(seq),
            "question_function": it["input"]["question_function"], "options": lines}


def vals_task5(it):
    lo, hi = it["input"]["antigen_region"]
    rbd = it["input"]["antigen"][lo - 1:hi]; ab = it["input"]["antibody"]; mut = it["input"]["mutation"]
    return {"vh": ab["H"], "cdr_h1": ab["cdr_h"][0], "cdr_h2": ab["cdr_h"][1], "cdr_h3": ab["cdr_h"][2],
            "vl": ab["L"], "cdr_l1": ab["cdr_l"][0], "cdr_l2": ab["cdr_l"][1], "cdr_l3": ab["cdr_l"][2],
            "antigen_len": len(rbd), "numbered_antigen": numbered(rbd, 1),
            "mut_pos": mut["position"] - lo + 1, "mut_wt": mut["wt"], "mut_mut": mut["mut"]}


VALS = {"task1": vals_task1, "task2": vals_task2, "task3": vals_task3, "task4": vals_task4, "task5": vals_task5}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cot", action="store_true", help="alias for --variant cot")
    ap.add_argument("--variant", default="",
                    help="prompt variant: reads prompts_<variant>/ -> rendered_data_<variant>.jsonl (e.g. cot, noncot)")
    args = ap.parse_args()
    variant = "cot" if args.cot else args.variant
    prompts_dir = f"{HERE}/prompts_{variant}" if variant else f"{HERE}/prompts"
    OUT = f"{HERE}/rendered_data_{variant}.jsonl" if variant else f"{HERE}/rendered_data.jsonl"
    n = 0
    with open(OUT, "w") as fh:
        for task in TASKS:
            sys, user_tpl = load_template(task, prompts_dir)
            items = [json.loads(l) for l in open(f"{RAW}/{task}.jsonl")]
            for it in items:
                user = user_tpl.format(**VALS[task](it))
                fh.write(json.dumps({"id": it["id"], "task": task,
                                     "primary_category": it["primary_category"],
                                     "system": sys, "user": user,
                                     "label": it["label"], "meta": it.get("meta", {})}) + "\n")
                n += 1
            print(f"  {task}: {len(items)} rendered")
    print(f"-> {OUT}  ({n} items)")


if __name__ == "__main__":
    main()
