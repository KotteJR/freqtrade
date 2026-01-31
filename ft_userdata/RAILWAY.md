# Deploy Freqtrade on Railway

This folder is set up to run [Freqtrade](https://www.freqtrade.io/) on [Railway](https://railway.app/) using the official Docker image.

## 1. Create a Railway project

1. Go to [railway.app](https://railway.app/) and create a project.
2. **New → GitHub repo** (or **Empty project** and connect repo later).
3. If you use the main freqtrade repo, set the **service root** to `ft_userdata` so Railway builds from this directory (where the Dockerfile and `railway.toml` live).

## 2. Add a Volume (recommended)

To keep config, database, and logs across deploys:

1. In your service → **Variables** tab → **Volumes**.
2. Add a volume and set the **mount path** to:  
   `/freqtrade/user_data`
3. Optionally set **RAILWAY_RUN_UID=0** if the app has permission issues with the volume (official image runs as non-root).

Data in `user_data` (e.g. `config.json`, `tradesv3.sqlite`, logs) will then persist.  
**Note:** If you use a volume, the first deploy will use the config baked into the image until you replace `config.json` on the volume (e.g. by copying your own file in or editing via a one-off run).

## 3. Environment variables

Set these in Railway (**Variables**):

| Variable | Required | Description |
|----------|----------|-------------|
| `FREQTRADE__exchange__key` | Yes (for live/dry-run with exchange) | Exchange API key |
| `FREQTRADE__exchange__secret` | Yes (for live/dry-run with exchange) | Exchange API secret |
| `FREQTRADE__api_server__username` | Recommended | API server login (default in config: `freqtrader`) |
| `FREQTRADE__api_server__password` | Recommended | API server password (default: `SuperSecurePassword`) |
| `FREQTRADE__api_server__jwt_secret_key` | Recommended | Random string for JWT (e.g. `openssl rand -hex 32`) |

`PORT` is set by Railway automatically; the entrypoint uses it for the API.

Any [Freqtrade config](https://www.freqtrade.io/en/stable/configuration/) can be overridden with env vars using the pattern:  
`FREQTRADE__<section>__<key>` (e.g. `FREQTRADE__exchange__name`, `FREQTRADE__dry_run`).

## 4. Deploy

Push to your connected branch; Railway will build the Dockerfile in `ft_userdata` and run the bot. The REST API will be available at the service URL Railway assigns (e.g. `https://your-service.up.railway.app`).

- **Healthcheck:** Railway pings `/api/v1/ping` to confirm the app is up.
- **API docs:** `https://your-service.up.railway.app/docs` (if the API is enabled and reachable).

## 5. Custom strategy

The default command uses `SampleStrategy`. To use your own strategy:

1. Put your strategy file in `user_data/strategies/` (e.g. in the repo under `ft_userdata/user_data/strategies/` so it’s in the image), or
2. Mount a volume at `/freqtrade/user_data` and place your strategy in `user_data/strategies/` on that volume.

Then set the start command in Railway to pass `--strategy YourStrategyName`, or add to `railway.toml`:

```toml
[deploy]
startCommand = "trade --config /freqtrade/user_data/config.json --logfile /freqtrade/user_data/logs/freqtrade.log --db-url sqlite:////freqtrade/user_data/tradesv3.sqlite --strategy YourStrategyName"
```

(You can also override the command in the Railway service **Settings**.)

## 6. Summary

- **Build:** Dockerfile in `ft_userdata` (FROM `freqtradeorg/freqtrade:stable`).
- **Port:** Taken from `PORT`; entrypoint sets `FREQTRADE__api_server__listen_port` and binds to `0.0.0.0`.
- **Config:** Default `user_data/config.json` in image; override with env vars and/or a volume at `/freqtrade/user_data`.
- **Restart:** `restartPolicyType = "ALWAYS"` in `railway.toml`.
