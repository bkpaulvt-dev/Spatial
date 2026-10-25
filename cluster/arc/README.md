# Running on VT ARC A100s

GPU jobs for this repo on Virginia Tech's Advanced Research Computing (ARC)
clusters, using the A100 nodes on Tinker Cliffs.

## 1. Log in

You need an ARC account and an allocation (request both through ARC's ColdFront
portal). Off campus, connect to the VT VPN first.

```bash
ssh <your_pid>@tinkercliffs1.arc.vt.edu      # password + Duo push
```

## 2. Get the code and data

```bash
git clone https://github.com/bkpaulvt-dev/Spatial.git && cd Spatial
# copy DLPFC data from your machine (run this locally, not on ARC):
#   scp -r data/DLPFC <your_pid>@tinkercliffs1.arc.vt.edu:~/Spatial/data/
```

Large data belongs in `/projects/<group>/` (shared, persistent) rather than home.
Pass its path with `DATA=/projects/.../DLPFC`.

## 3. Build the environment (once)

```bash
bash cluster/arc/setup_env.sh
```

## 4. Submit

```bash
sbatch --account=<your_allocation> cluster/arc/run_a100.sbatch
# a smaller test first:
sbatch --account=<your_allocation> -t 00:30:00 cluster/arc/run_a100.sbatch \
    --methods hicast --slices 151673 --seeds 0
# a new variant:
sbatch --account=<your_allocation> cluster/arc/run_a100.sbatch \
    --methods hicast --config no_lg='{"local_global": false}'
```

Environment overrides: `DATA`, `OUT`, `WORKERS`, `ENV`.

## 5. Monitor

```bash
squeue -u $USER
tail -f logs/spatial-a100-<jobid>.out
scancel <jobid>
```

Results append to `results/dlpfc_a100_<jobid>.jsonl`; reruns with the same `OUT`
skip finished runs. For interactive debugging:

```bash
interact -A <your_allocation> -p a100_normal_q --gres=gpu:1 -t 1:00:00
```
