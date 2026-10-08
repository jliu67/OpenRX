#!/bin/bash
set -eu
umask 077
mkdir -p /tmp/openrx-stream-review-l90j6zsq/guest
cd /tmp/openrx-stream-review-l90j6zsq/guest
: # synthetic review omits inventory output
base64 -d > runtime <<'OPENRX_BINARY_BASE64'
IyEvYmluL2Jhc2gKcHJpbnRmICclc1xuJyAneyJzeW50aGV0aWMiOiJjYXB0dXJlLWZhaWx1cmUifScKZXhpdCAwCg==
OPENRX_BINARY_BASE64
printf '%s  %s\n' '9fe1bea5c9fb4cacdbd928a38e9a4932d74141dca449001c65290dfb6ada08da' 'runtime' | sha256sum -c -
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
