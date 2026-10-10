#!/usr/bin/python3
import datetime, json, os, pathlib, socket, sys, time
folder = pathlib.Path(sys.argv[1]); mode = sys.argv[2]
log = folder / (mode + '-finalizer.jsonl')
start = time.monotonic()
def record(event):
    with log.open('a') as stream:
        stream.write(json.dumps({'event': event, 'elapsed': time.monotonic()-start, 'pid': os.getpid(), 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})+'\n')
        stream.flush(); os.fsync(stream.fileno())
record('started')
address = os.environ.get('NOTIFY_SOCKET')
record('socket_present' if address else 'socket_absent')
while time.monotonic()-start < 8:
    if mode != 'none':
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            sock.sendto(b'EXTEND_TIMEOUT_USEC=5000000', ('\0'+address[1:]) if address.startswith('@') else address)
        record('notification_sent')
    time.sleep(1)
record('finished')
