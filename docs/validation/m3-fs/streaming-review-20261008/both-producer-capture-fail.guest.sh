#!/bin/bash
set -eu
umask 077
mkdir -p /tmp/openrx-stream-review-98cah5id/guest
cd /tmp/openrx-stream-review-98cah5id/guest
: # synthetic review omits inventory output
base64 -d > runtime <<'OPENRX_BINARY_BASE64'
IyEvYmluL2Jhc2gKcHJpbnRmICclc1xuJyAneyJzeW50aGV0aWMiOiJib3RoLWZhaWwifScKZXhpdCA0Mgo=
OPENRX_BINARY_BASE64
printf '%s  %s\n' '2a1eb6853139366c470d97e17b31349a8ef55696570e9671d3290781261abb7c' 'runtime' | sha256sum -c -
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
