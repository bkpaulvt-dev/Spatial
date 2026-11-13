# G3 re-tests on the new datasets

Verdict rule (pre-registered): with d0 = sign(S0 - n0), 'replicates' if d0*(S - n0) > 0 and the 95% bootstrap interval excludes n0; 'reverses' if d0*(S - n0) < 0 with the interval excluding n0; otherwise 'weakens'. Intervals are bootstrap over replicates (simulation) or sections (real data); with few units they are wide.

Original reference S0 (pooled over the original datasets): a=0.164, d=0.214, b=0.113, c=0.004, e=0.015

| unit | finding | n units | S (95% CI) | n0 | S0 | verdict |
|---|---|---|---|---|---|---|
| allenmerfish | a | 3 | 0.141 (0.112 to 0.167) | 0.03 | 0.164 | replicates |
| allenmerfish | b | 3 | 0.119 (0.110 to 0.136) | 0.03 | 0.113 | replicates |
| allenmerfish | c | 3 | -0.019 (-0.036 to -0.007) | 0.0 | 0.004 | reverses |
| allenmerfish | d | 3 | 0.014 (-0.186 to 0.292) | 0.0 | 0.214 | weakens |
| allenmerfish | e | 3 | 0.014 (-0.018 to 0.038) | 0.0 | 0.015 | weakens |
