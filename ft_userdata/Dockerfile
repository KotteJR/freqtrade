# Railway deployment: use official image and wire PORT + user_data
FROM freqtradeorg/freqtrade:stable

# Entrypoint sets FREQTRADE__api_server__listen_port=$PORT and listen_ip_address=0.0.0.0
COPY entrypoint.sh /entrypoint.sh

# Default config (override via FREQTRADE__* env vars). Keep a copy for fresh volumes.
COPY user_data/config.json /default_config.json
COPY user_data/config.json /freqtrade/user_data/config.json
# Your custom strategies (add .py files in ft_userdata/user_data/strategies/)
COPY user_data/strategies/ /freqtrade/user_data/strategies/
# Official flow: create-userdir fills strategies/ with SampleStrategy if missing (docs/docker_quickstart.md)
RUN freqtrade create-userdir --userdir /freqtrade/user_data

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
CMD ["trade", "--config", "/freqtrade/user_data/config.json", "--logfile", "/freqtrade/user_data/logs/freqtrade.log", "--db-url", "sqlite:////freqtrade/user_data/tradesv3.sqlite"]
