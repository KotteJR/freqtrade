#!/bin/sh
# Railway sets PORT; freqtrade expects api_server.listen_port.
# Override via env so the API listens on Railway's port and on 0.0.0.0.
export FREQTRADE__api_server__listen_port="${PORT:-8080}"
export FREQTRADE__api_server__listen_ip_address="${FREQTRADE__api_server__listen_ip_address:-0.0.0.0}"
exec freqtrade "$@"
