"""Loaded automatically by every python process that has this folder on PYTHONPATH (set by newdata_queue.py, review_queue.py and the review stage helper): limits BLAS/OpenMP thread pools to 1
without touching bench_run.py or any method code. numba/numexpr/torch pools are limited by the environment variables set at the same place. Failure to import threadpoolctl is ignored."""
try:
    from threadpoolctl import threadpool_limits
    threadpool_limits(limits=1)
except Exception:
    pass
