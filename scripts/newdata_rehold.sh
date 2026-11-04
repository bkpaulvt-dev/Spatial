#!/bin/bash
# One-shot helper (Amendment 2 follow-up): tier 1 of the simulation was restarted behind the hold file; the hold is removed for tier 1 and put back the moment tier 1 is reported done,
# so the real-data phase (Allen MERFISH) still goes before tiers 2-3, as before. Phase 2 removes the hold itself afterwards.
S=/mnt/disk/bikashkumar/SpatialBench
rm -f $S/newdata_hold
until grep -q "tier (cheapest 5 methods) done" $S/newdata_status.txt; do sleep 1; done
touch $S/newdata_hold; echo "$(date '+%F %T') [rehold] hold file restored after tier 1" >> $S/newdata_status.txt
