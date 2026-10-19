# EXP-023: full default hardware-dataset hash

Status: source prepared for independent method review and local admission. No new
native reference, model build, calibration prefix or complete RTL run has executed
for this experiment. Base is PR #82 merge `fa0bc79bdcd89c91aab11596b6f7f5e104aa6884`.

The [new admitted driver](../scripts/test_dataset_fullhash.py) targets exactly one
RandomX v2 8×2,048 ideal-service lifecycle using the accepted capacity wrapper,
dataset item, superscalar executor and multiplier. Existing arithmetic and lifecycle
RTL remain unchanged. This is distinct from EXP-022 protocol stress and its 2×1
connected results.

The old full connected reference used a different key/input. Its gold cannot serve
as the oracle for the retained cache0 context. The new reference adapter loads the
same seven accepted cache0/program/239-reciprocal assets and unchanged native
archive, then executes the unchanged pinned lifecycle reference algorithm and
`randomx_calculate_hash` canonical comparison. It creates new compatible full gold;
it does not regenerate accepted Argon2/cache images, superscalar programs or
reciprocal tables. The scoped adapter limits and closes exactly 16,384 direct native
dataset calls and exports each full address/data assertion. The original two-item
reference adapter and its trusted lock stay byte-identical.

Preparation is a separate admitted step. `--prepare-only` runs the small new
synthetic accounting/identity tests, compiles that reference, generates full gold
and compiles one Verilator model. It never executes the RTL hash. All source,
commands, gold, executable, original assets, archive and tool identities are retained.
The later full run requires `--prepared-output` and its externally pinned
`--prepared-manifest-sha256`; actual consumed bytes and command outcomes are checked
again rather than trusting embedded digest strings. Source must remain clean and
at the exact preparation tree.

The retained testbench compares every dataset address and 64-byte result, all
16,384 iteration R/F/E/A/rounding/address/control/route states and bytecode accesses,
all program images, seven hardware seed transitions, each complete 2 MiB program
boundary, final registers and digest. Assertions never supply oracle values to
the DUT. The full validator closes all demand/response, namespace, stage,
instruction and clock ledgers and requires zero live software input/fill/program/
dataset callbacks. Native assertion callbacks remain separately counted.

The testbench's original 200,000,000-clock watchdog remains its default. The full
driver selects 1,500,000,000 clocks with explicitly 64-bit delay arithmetic, below
signed cycle-counter overflow; its positive wall-time budget is separately required.
Event trace mode avoids a line for every dataset wait clock. Progress JSONL, item
CSV, trace and standard output flush every 64 completed items and at program
boundaries. A stopped prefix provides calibration/failure evidence, never a full
hash or a resumable checkpoint.

The fixed cache0 programs imply 53,325 ideal executor, 53,399 core and 53,400
session clocks per item, including one launch clock. The 16,384-item availability
sum is 874,905,600 clocks; all dataset clocks remain nested inside outer execution.
These are input-derived accounting expectations, not a new measured full-run
result or a wall-time bound. Admission must use fresh host metrics and measured
backend progress before committing a materially long run.

Host preparation, tagged immutable cache/program/reciprocal responses and the
scratchpad memory model remain explicit. Their modeled service timing does not
establish a physical memory/bank/controller implementation. Physical PPA,
calibrated frequency, architecture selection and the 1 MH/s below 2,500 W target
remain unproven even if this functional hash completes.
