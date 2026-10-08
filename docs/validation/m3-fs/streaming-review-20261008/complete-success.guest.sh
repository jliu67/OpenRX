#!/bin/bash
set -eu
umask 077
mkdir -p /tmp/openrx-stream-review-sqdmyd1i/guest
cd /tmp/openrx-stream-review-sqdmyd1i/guest
: # synthetic review omits inventory output
base64 -d > runtime <<'OPENRX_BINARY_BASE64'
IyEvYmluL2Jhc2gKcHJpbnRmICclc1xuJyAneyJzeW50aGV0aWMiOiJjb21wbGV0ZSJ9JwpleGl0IDAK
OPENRX_BINARY_BASE64
printf '%s  %s\n' '80561f2152bd183cb91517ae57a77f06b75a2d7405bb867179f1f1d32a53a415' 'runtime' | sha256sum -c -
chmod 700 runtime
printf 'OPENRX_RUNTIME_BEGIN\n'
set +e
./runtime 2> runtime.stderr | tee runtime.jsonl
statuses=("${PIPESTATUS[@]}")
status=${statuses[0]}
capture_status=${statuses[1]}
set -e
if [ "$capture_status" -ne 0 ]; then exit "$capture_status"; fi
printf 'OPENRX_RUNTIME_END status=%s\n' "$status"
printf 'OPENRX_RUNTIME_STDERR_BEGIN\n'
cat runtime.stderr
printf 'OPENRX_RUNTIME_STDERR_END\n'
if [ "$status" -ne 0 ]; then exit "$status"; fi
printf 'OPENRX_GUEST_COMPLETE\n'
