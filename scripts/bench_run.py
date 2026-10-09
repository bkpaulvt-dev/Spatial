"""Run ONE job: (method, dataset, section, seed) -> results/runs/<id>.json and <id>.npz

Saves per-spot predictions (official and matched clustering), the full metric panel for both, and
the method's own timing. Never raises for a method failure: the record carries status='error'.
"""
import argparse, json, os, sys, time, traceback, warnings
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
warnings.filterwarnings("ignore")


def job_id(ds, sec, method, seed):
    return f"{ds}__{sec}__{method}__s{seed}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True); ap.add_argument("--dataset", required=True)
    ap.add_argument("--section", required=True); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "runs"))
    ap.add_argument("--save-emb", action="store_true", help="also save the embedding (seed 0 recommended)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    jid = job_id(args.dataset, args.section, args.method, args.seed)
    rec = {"id": jid, "method": args.method, "dataset": args.dataset, "section": args.section, "seed": args.seed}
    try:
        import torch; torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", 1)))
        from adapters import ADAPTERS
        from anisost import robust_gmm
        from spatialbench import metrics as M
        from spatialbench.data import load_section
        a = load_section(args.dataset, args.section)
        truth = a.obs["ground_truth"].to_numpy(dtype=object)
        coords = np.asarray(a.obsm["spatial"], float)
        valid = M.valid_mask(truth)
        k = int(len(set(truth[valid].astype(str))))
        rec.update(K=k, n_obs=int(a.n_obs), n_vars=int(a.n_vars))
        t0 = time.time()
        res = ADAPTERS[args.method](a, k, args.seed, args.dataset)
        rec["method_s"] = time.time() - t0
        lab, emb = np.asarray(res["labels"]), res["emb"]
        rec["k_found"] = int(len(np.unique(lab)))
        rec["extra"] = {k_: float(v) if np.isscalar(v) else v for k_, v in res["extra"].items()}
        full = M.evaluate(lab, truth, coords, emb=emb)
        rec["per_domain"] = M.per_domain(lab, truth)["per_domain"]
        rec["metrics"] = {k_: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v)
                          for k_, v in full.items() if k_ != "per_domain"}
        save = {"labels": lab, "valid": valid}
        if emb is not None:
            lab_m = robust_gmm(np.asarray(emb, float), k, seed=args.seed)
            fm = M.evaluate(lab_m, truth, coords, emb=emb)
            rec["metrics_matched"] = {k_: float(v) for k_, v in fm.items() if isinstance(v, (int, float, np.floating, np.integer))}
            save["labels_matched"] = lab_m
            if args.save_emb:
                save["emb"] = np.asarray(emb, np.float32)
        np.savez_compressed(os.path.join(args.out, jid + ".npz"), **save)
        rec["status"] = "ok"
    except Exception as e:  # noqa: BLE001  (a method failure is a result, not a crash)
        rec.update(status="error", error=f"{type(e).__name__}: {e}"[:1500], trace=traceback.format_exc()[-1500:])
    json.dump(rec, open(os.path.join(args.out, jid + ".json"), "w"))
    print("RESULT " + jid + " " + rec["status"], flush=True)


if __name__ == "__main__":
    main()
