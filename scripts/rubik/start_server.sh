#!/bin/bash
# Start the API server in background without blocking
# Uses lsof for safe kill (avoids pkill self-match hang)

cd /home/igrek/src/igrek51.github.io

# Kill any existing server on port 8080 using lsof (safe, no self-match)
pid=$(lsof -ti :8080 2>/dev/null)
[ -n "$pid" ] && kill "$pid" 2>/dev/null && echo "Killed old server PID $pid" >&2

# Start server with output redirection, detached
python scripts/rubik/test_server.py 8080 0.0.0.0 > /tmp/server.log 2>&1 &

# Print PID
echo $!

# Wait a moment for startup
sleep 1

# Check if it's running
if lsof -ti :8080 > /dev/null 2>&1; then
    echo "Server started successfully" >&2
    tail -5 /tmp/server.log >&2
else
    echo "Server failed to start" >&2
    [ -s /tmp/server.log ] && cat /tmp/server.log >&2
fi
