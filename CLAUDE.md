# Notes for Claude Code sessions in this repository

## Disk rule on the lab server DeepMed2 (always)
The root disk `/` of DeepMed2 is shared and can be 100% full. **Never write temporary files, caches, installs, environments, data or results to `/`
(including `/tmp` and the home folder).** Everything goes under `/mnt/disk/bikashkumar/SpatialBench` (about 6 TB free).
- Every script starts with `. "$(dirname "$0")/deepmed2_env.sh"` (it sets TMPDIR, pip/conda/R/Hugging Face/torch caches under that folder) and calls `disk_guard`
  before each stage. In an interactive shell run `. /mnt/disk/bikashkumar/SpatialBench/Spatial/scripts/deepmed2_env.sh` first.
- New conda environments: `conda create -p /mnt/disk/bikashkumar/SpatialBench/envs/<name>`; R packages: `$BASE/Rlib` or `$BASE/Rlib_extra`, never `~/R/library`.
- **Never use `~/shared_disk` (`/home/bikashkumar/shared_disk`) for anything**: no data, no environments, no caches, no results, no reads for our work, and never move, rename or delete anything in it. It is not ours to use. Keep all work under `/mnt/disk/bikashkumar/SpatialBench`.
- Delete only files you created. Never use `pkill -f` or `pgrep -f`; stop processes by PID or process group.

## Project rules
See `docs/DEEPMED2_RUNBOOK.md` and `docs/DEEPMED2_NEXT.md`: do not change existing method code or settings; never write credentials; honest reporting of failures.
