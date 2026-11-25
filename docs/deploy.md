# Deploying to the homelab

Laner Money runs in Docker on the homelab and is reachable **only over
Tailscale, with HTTPS**. The container listens on `127.0.0.1` on the host
(not the LAN, not the internet). Tailscale Serve on the same host adds
HTTPS for devices on the tailnet.

```
phone/laptop ──tailnet (WireGuard)──▶ tailscale serve :443 (HTTPS)
                                        └─▶ 127.0.0.1:8000 ─▶ laner-money container
```

## Requirements on the Docker host

- Docker with the compose plugin (`docker compose version`).
- Tailscale running **on the same machine as Docker** (`tailscale status`).
- In the Tailscale admin console → DNS: **MagicDNS** and **HTTPS
  certificates** turned on (needed for `https://….ts.net`).

If Tailscale runs somewhere else (e.g. on the Proxmox host, but Docker is
in a VM or LXC), install Tailscale inside that VM/LXC too. Otherwise
`tailscale serve` can't reach `127.0.0.1:8000`.

## First install

```bash
git clone git@github.com:JaheimT/laner-money.git   # or copy the folder over
cd laner-money
cp .env.example .env              # check TZ / LANER_PORT; no secrets in it
docker compose up -d --build
docker compose ps                 # laner-money should become "healthy"

# Set the login password (asked twice, at least 12 characters):
docker compose exec laner python -m app.cli set-password

# HTTPS on the tailnet:
sudo tailscale serve --bg 8000
tailscale serve status            # shows the https://<host>.<tailnet>.ts.net URL
```

Open that URL on your phone (with Tailscale connected) and log in.

- If port 443 is already used by another service's Tailscale Serve, give
  Laner its own port: `sudo tailscale serve --bg --https=8443 8000`, then
  use `https://<host>.<tailnet>.ts.net:8443`.
- If `LANER_PORT` in `.env` isn't 8000, use that number instead of 8000.
- **Never use `tailscale funnel`** for this. Funnel puts it on the public
  internet.
- Cookies are `Secure`, so login only works over HTTPS (the ts.net URL) or
  on `localhost`. A plain `http://<ip>:8000` won't work. That's on purpose.

Tip: add it to your phone's home screen from the browser menu.

## Updating

```bash
cd laner-money
git pull
docker compose up -d --build
```

Database migrations run automatically when the app starts.

## Backups

The `backup` container makes a checked copy of the database when it
starts, then every night at `BACKUP_HOUR`. It keeps the newest
`BACKUP_KEEP`.

```bash
docker compose logs backup                     # "Backup written: ..."
docker compose exec backup python -m app.backup  # make one right now
docker compose cp backup:/backups ./laner-backups   # copy them off the container
```

These backups live on the same machine as the database. Copying them
somewhere else (another disk, another machine) is still to do (roadmap
M4 step 4).

### Restore (not yet rehearsed: roadmap M4 step 4)

```bash
docker compose exec backup ls /backups          # pick one
docker compose stop laner
# cp runs as the container's own user, so file ownership stays right:
docker compose exec backup cp /backups/laner-YYYY-MM-DDTHHMMSS.db /data/laner.db
docker compose start laner
```

## Useful commands

```bash
docker compose logs -f laner          # app logs
docker compose restart laner          # restart (clears the login lockout)
docker compose exec laner python -m app.cli set-password   # change password; logs out every device
```
