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
| sim_bands:m=1 | a | 5 | 0.262 (0.250 to 0.275) | 0.03 | 0.164 | replicates |
| sim_bands:m=1 | b | 5 | 0.012 (0.003 to 0.022) | 0.03 | 0.113 | reverses |
| sim_bands:m=1 | c | 5 | 0.032 (0.023 to 0.042) | 0.0 | 0.004 | replicates |
| sim_bands:m=1 | d | 5 | 0.684 (0.630 to 0.737) | 0.0 | 0.214 | replicates |
| sim_bands:m=1 | e | 5 | 0.089 (0.063 to 0.112) | 0.0 | 0.015 | replicates |
| sim_bands:m=2 | a | 5 | 0.264 (0.251 to 0.277) | 0.03 | 0.164 | replicates |
| sim_bands:m=2 | b | 5 | 0.015 (0.003 to 0.032) | 0.03 | 0.113 | weakens |
| sim_bands:m=2 | c | 5 | 0.062 (0.051 to 0.077) | 0.0 | 0.004 | replicates |
| sim_bands:m=2 | d | 5 | 0.833 (0.791 to 0.869) | 0.0 | 0.214 | replicates |
| sim_bands:m=2 | e | 5 | 0.100 (0.079 to 0.118) | 0.0 | 0.015 | replicates |
| sim_bands:m=4 | a | 5 | 0.234 (0.220 to 0.248) | 0.03 | 0.164 | replicates |
| sim_bands:m=4 | b | 5 | 0.009 (0.004 to 0.017) | 0.03 | 0.113 | reverses |
| sim_bands:m=4 | c | 5 | 0.043 (0.029 to 0.055) | 0.0 | 0.004 | replicates |
| sim_bands:m=4 | d | 5 | 0.708 (0.615 to 0.779) | 0.0 | 0.214 | replicates |
| sim_bands:m=4 | e | 5 | 0.097 (0.087 to 0.106) | 0.0 | 0.015 | replicates |
| sim_bands:m=7 | a | 5 | 0.236 (0.208 to 0.265) | 0.03 | 0.164 | replicates |
| sim_bands:m=7 | b | 5 | 0.042 (0.025 to 0.057) | 0.03 | 0.113 | weakens |
| sim_bands:m=7 | c | 5 | 0.031 (0.023 to 0.040) | 0.0 | 0.004 | replicates |
| sim_bands:m=7 | d | 5 | 0.707 (0.628 to 0.785) | 0.0 | 0.214 | replicates |
| sim_bands:m=7 | e | 5 | 0.070 (0.058 to 0.083) | 0.0 | 0.015 | replicates |
| sim_blocks:w=12 | a | 5 | 0.237 (0.213 to 0.261) | 0.03 | 0.164 | replicates |
| sim_blocks:w=12 | b | 5 | 0.049 (0.033 to 0.066) | 0.03 | 0.113 | replicates |
| sim_blocks:w=12 | c | 5 | 0.031 (0.023 to 0.040) | 0.0 | 0.004 | replicates |
| sim_blocks:w=12 | d | 5 | 0.791 (0.716 to 0.857) | 0.0 | 0.214 | replicates |
| sim_blocks:w=12 | e | 5 | 0.081 (0.072 to 0.091) | 0.0 | 0.015 | replicates |
| sim_blocks:w=20 | a | 5 | 0.241 (0.205 to 0.276) | 0.03 | 0.164 | replicates |
| sim_blocks:w=20 | b | 5 | 0.069 (0.046 to 0.095) | 0.03 | 0.113 | replicates |
| sim_blocks:w=20 | c | 5 | 0.027 (0.012 to 0.042) | 0.0 | 0.004 | replicates |
| sim_blocks:w=20 | d | 5 | 0.673 (0.580 to 0.765) | 0.0 | 0.214 | replicates |
| sim_blocks:w=20 | e | 5 | 0.021 (-0.008 to 0.049) | 0.0 | 0.015 | weakens |
| sim_blocks:w=3 | a | 5 | 0.212 (0.183 to 0.235) | 0.03 | 0.164 | replicates |
| sim_blocks:w=3 | b | 5 | 0.059 (0.037 to 0.078) | 0.03 | 0.113 | replicates |
| sim_blocks:w=3 | c | 5 | 0.048 (0.037 to 0.060) | 0.0 | 0.004 | replicates |
| sim_blocks:w=3 | d | 5 | 0.596 (0.493 to 0.699) | 0.0 | 0.214 | replicates |
| sim_blocks:w=3 | e | 5 | 0.049 (0.025 to 0.072) | 0.0 | 0.015 | replicates |
| sim_blocks:w=5 | a | 5 | 0.281 (0.267 to 0.294) | 0.03 | 0.164 | replicates |
| sim_blocks:w=5 | b | 5 | 0.048 (0.031 to 0.067) | 0.03 | 0.113 | replicates |
| sim_blocks:w=5 | c | 5 | 0.045 (0.031 to 0.063) | 0.0 | 0.004 | replicates |
| sim_blocks:w=5 | d | 5 | 0.672 (0.560 to 0.797) | 0.0 | 0.214 | replicates |
| sim_blocks:w=5 | e | 5 | 0.050 (0.036 to 0.065) | 0.0 | 0.015 | replicates |
| sim_blocks:w=8 | a | 5 | 0.267 (0.238 to 0.295) | 0.03 | 0.164 | replicates |
| sim_blocks:w=8 | b | 5 | 0.057 (0.047 to 0.067) | 0.03 | 0.113 | replicates |
| sim_blocks:w=8 | c | 5 | 0.034 (0.027 to 0.044) | 0.0 | 0.004 | replicates |
| sim_blocks:w=8 | d | 5 | 0.779 (0.701 to 0.848) | 0.0 | 0.214 | replicates |
| sim_blocks:w=8 | e | 5 | 0.070 (0.048 to 0.091) | 0.0 | 0.015 | replicates |
