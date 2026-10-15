#!/bin/sh
# Finish the coverage-fill benchmark with the reduced plan: CCST with 3 seeds, DeepST and BayesSpace with seed 0
# only, then retry runs that failed (mostly out of memory) one at a time, then rebuild the supplement.
# Safe to re-run: finished jobs are skipped.  Start with:  nohup sh scripts/run_fill_v2.sh > fill.log 2>&1 &
# Never run deepst / bayesspace / nichepca at the same time as other jobs (memory: 15 GB container).
#   WAIT_PID: optional PID of an already running queue to wait for first.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
if [ -n "$WAIT_PID" ]; then while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 60; done; fi
python scripts/bench_queue.py --methods spatial_mgcn ccst --seeds 0 1 2 --workers 3
python scripts/bench_queue.py --methods deepst bayesspace --seeds 0 --workers 1
python scripts/bench_queue.py --methods spagcn bass stagate spaceflow graphst nichepca sedr spatial_mgcn ccst --seeds 0 1 2 --workers 1 --retry-errors
python scripts/bench_queue.py --methods deepst bayesspace --seeds 0 --workers 1 --retry-errors
echo FILL_FINISHED
# rebuild supplementary tables, check numbers, publish
python scripts/coverage_matrix.py
python scripts/make_supplement.py
(cd paper && pdflatex -interaction=nonstopmode supplementary >/dev/null; pdflatex -interaction=nonstopmode supplementary >/dev/null)
python scripts/check_paper_numbers.py
git add results/benchmark_runs.jsonl results/coverage_matrix.* results/supp paper/supplementary.tex paper/supp_labels.tex paper/supplementary.pdf
git commit -q -m "Coverage fill finished; rebuild supplementary tables

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01EcsLQxEmDfiYDfyMQq2kQw" && git push -q origin claude/great-cori-opzfx7
scripts/push_overleaf.sh "" "Supplementary tables after coverage fill"
echo ALL_DONE
