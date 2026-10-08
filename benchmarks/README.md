# Measurements

Use scripts/benchmark.py. It records source/build context, CPU information, command lines, timestamps, output hashes and raw logs. Verification-mode smoke runs establish execution only. Formal baseline: full dataset, adequate warmup, repeated long runs, controlled affinity/thermal settings, unchanged compiler and pages. Optional flags do not change host configuration automatically.

Power is not sampled by this runner. Measure average wall power over the steady-state hash interval and document meter, sample interval, idle power and the components included. H/J = H/s ÷ W; J/kH = 1000 × W ÷ H/s. Keep raw samples. Never substitute CPU TDP for measured power.

Local runs are ignored by default. Force-add selected result directories with an experiment report after reviewing host metadata for private details. CI artifacts are functional evidence only.
