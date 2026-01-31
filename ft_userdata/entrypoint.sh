#!/bin/sh
# Railway sets PORT; freqtrade expects api_server.listen_port.
# Override via env so the API listens on Railway's port and on 0.0.0.0.
export FREQTRADE__api_server__listen_port="${PORT:-8080}"
export FREQTRADE__api_server__listen_ip_address="${FREQTRADE__api_server__listen_ip_address:-0.0.0.0}"
# If user_data is a fresh volume, set up like official create-userdir (config + SampleStrategy)
if [ ! -f /freqtrade/user_data/config.json ]; then
  cp /default_config.json /freqtrade/user_data/config.json
fi
if [ ! -f /freqtrade/user_data/strategies/sample_strategy.py ]; then
  freqtrade create-userdir --userdir /freqtrade/user_data
fi
exec freqtrade "$@"
