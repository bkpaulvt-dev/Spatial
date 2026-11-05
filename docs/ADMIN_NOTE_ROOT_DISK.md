# Note for the admin: root disk of DeepMed2 is full (not committed)

Written 2026-11-04 18:14:58 (server time) by Bikash Kumar Paul's Claude Code session.

**Root disk 100% full, 5.3 GB free (/dev/nvme0n1p2, 1.8 TB); /mnt/disk (/dev/sda1) has 6.2 TB free. Please check.**

Largest top-level folders on / (du -x, read-only):

| Folder | Size |
|---|---|
| /home (all users) | 1.3 T |
| /tmp | 91 G (mostly other users; e.g. /tmp/bensyc_mbert_* folders of 10 G each) |
| /usr | 13 G |
| /var | 5.3 G |
| /boot | 160 M |

Inside my own home (/home/bikashkumar, 154 G, older material, not from the current project): shared_disk 109 G, .cache/huggingface 35 G, .vscode-server 6.9 G.
My files in /tmp: under 1 GB (session scratch files). The SpatialBench project (jobs, data, environments, caches) lives only under /mnt/disk/bikashkumar/SpatialBench; since 2026-11-04 its
scripts set TMPDIR and all caches there. Earlier jobs started before that change may have used /tmp for short-lived temporary files (no open files on / found at the time of the check).
Nothing was deleted except my own failed-install temp folder (11 MB) and 7 R packages my first install attempt put into ~/R/library by mistake.
