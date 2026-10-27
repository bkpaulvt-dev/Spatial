# Handoff: run this project on TinkerCliffs (VT ARC)

Paste the "Prompt for the new chat" section into a Claude Code session running
**on your own Mac** (Claude Desktop → Code → local, or `claude` in Terminal).

## Where the project stands

* Repo: `bkpaulvt-dev/Spatial`, branch `claude/bold-knuth-opoo9b`.
* `hicast/histar.py`: PyTorch port of the official HiSTaR code.
* `hicast/model.py`: HiCAST, the proposed successor model.
* `scripts/benchmark_dlpfc.py`: resumable, parallel benchmark (methods × slices × seeds).
  It appends one JSON line per run and skips finished runs on restart.
* `results/dlpfc_main.jsonl`: full run already done (12 DLPFC slices × 3 seeds ×
  `histar`, `histar_deterministic`, `hicast` = 108 lines). Median ARI: HiCAST 0.493
  vs HiSTaR 0.509 (p = 0.68). HiCAST does not beat HiSTaR yet.
* Write-up: `docs/HiCAST.md` (§5–6 have results and lessons).
* Code runs on CPU by default (`device="cpu"`); ~2 min per run per core.

## To do

1. On the Mac, check you can log in yourself (approve Duo):
   `ssh bikashkumar@tinkercliffs2.arc.vt.edu`
   Then set up an SSH key and connection reuse (see below) so Claude can run
   `ssh`/`scp` without asking for Duo every time.
2. On TinkerCliffs: clone the repo, create a Python env, install `requirements.txt`.
3. Download the 12 DLPFC slices into `~/Spatial/data/DLPFC/<slice>/`.
4. Submit `scripts/tinkercliffs_job.sh` with Slurm (fill in your allocation account).
5. Reproduce the main benchmark, then run new experiments (ablations, more seeds,
   GPU runs, held-out-donor tuning) with `--config NAME=JSON`.
6. Copy results back, commit them to the branch, push.

## Prompt for the new chat

```
I'm continuing my spatial transcriptomics project (repo bkpaulvt-dev/Spatial,
branch claude/bold-knuth-opoo9b). Read HANDOFF.md, README.md and docs/HiCAST.md first.

Goal: run the benchmark on Virginia Tech's TinkerCliffs cluster.
Login: ssh bikashkumar@tinkercliffs2.arc.vt.edu (Duo 2FA; I have already logged in
once in another terminal with ControlMaster, so reuse that connection).
Do NOT ask me for my password; use my SSH key/existing connection.

Steps:
1. Over ssh: check `sinfo`, `module avail` (Miniconda/Anaconda), and which Slurm
   account I can use (`sacctmgr show assoc user=bikashkumar` or ask me).
2. Clone the repo on TinkerCliffs into ~/Spatial (branch claude/bold-knuth-opoo9b),
   create a conda env "spatial" with python 3.11, pip install -r requirements.txt.
3. Download DLPFC data into ~/Spatial/data/DLPFC/<slice>/ for slices
   151507 151508 151509 151510 151669 151670 151671 151672 151673 151674 151675 151676:
   - filtered_feature_bc_matrix.h5 from
     https://spatial-dlpfc.s3.us-east-2.amazonaws.com/h5/<slice>_filtered_feature_bc_matrix.h5
   - metadata.tsv from GitHub repo JinmiaoChenLab/SEDR_analyses, path data/DLPFC/<slice>/metadata.tsv
     (raw.githubusercontent.com; check whether the branch is main or master).
4. Run one quick test (one slice, one seed) on an interactive node, then fill in
   the account/partition in scripts/tinkercliffs_job.sh and sbatch it.
5. Monitor with squeue; when done, scp results/*.jsonl back to my Mac,
   summarise median ARI per method, commit and push to the branch.
```

## SSH setup on the Mac (do this yourself once)

```bash
# 1. key (if you don't have one)
ssh-keygen -t ed25519
ssh-copy-id bikashkumar@tinkercliffs2.arc.vt.edu   # approve Duo once

# 2. reuse one approved connection, so Duo is needed only once per session
cat >> ~/.ssh/config <<'EOF'
Host tc
    HostName tinkercliffs2.arc.vt.edu
    User bikashkumar
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 8h
EOF

# 3. open the connection (approve Duo), keep this terminal open
ssh tc
```

After this, Claude (running on your Mac) can use `ssh tc '...'` and
`scp file tc:~/...` without the password or another Duo prompt.

**Never paste your password into a chat.** Change your VT password if you already did.
