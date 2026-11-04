"""bench_run.py with the extra methods of scripts/review_methods.py registered (adapters.py and bench_run.py stay untouched).
Same command line and output as bench_run.py. Used by scripts/review_queue.py."""
import os, runpy, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [ROOT, HERE]
if "--section" in sys.argv: os.environ["REVIEW_SECTION"] = sys.argv[sys.argv.index("--section") + 1]   # adapters get no section argument; group methods need it
import adapters, review_methods  # noqa: E402
adapters.ADAPTERS.update(review_methods.ADAPTERS)
sys.argv[0] = os.path.join(HERE, "bench_run.py")
runpy.run_path(sys.argv[0], run_name="__main__")
