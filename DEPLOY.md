# Deploy (VPS + GitHub Actions)

Production runs on the VPS at `/root/projects/ppgcomdata` with `docker-compose.prod.yml` (postgres, api, web).

## Automated deploy (GitHub Actions)

Workflow: [`.github/workflows/deploy-vps.yml`](.github/workflows/deploy-vps.yml)

- **Push to `main`** — runs when changes touch `apps/web`, `apps/api`, `docker-compose.prod.yml`, or deploy scripts.
- **Manual** — Actions → *Deploy to VPS* → *Run workflow* (optional `--no-cache` for web or all services).

### Required GitHub secrets

| Secret | Description |
|--------|-------------|
| `VPS_HOST` | Hostname or IP of the VPS |
| `VPS_USER` | SSH user (e.g. `root`) |
| `VPS_SSH_KEY` | Private SSH key (entire key, including `-----BEGIN ...-----`) |

### Optional secret

| Secret | Description |
|--------|-------------|
| `VPS_PORT` | SSH port (default `22`) |

Do **not** commit keys or `.env` production values to the repository.

### VPS prerequisites (one-time)

1. Clone the repo on the server:
   ```bash
   mkdir -p /root/projects && cd /root/projects
   git clone https://github.com/lucasreino/PPGCOMDATA.git ppgcomdata
   cd ppgcomdata
   ```
2. Configure `.env` / compose env for production (DB password, `JWT_SECRET`, `NEXT_PUBLIC_API_URL`, etc.).
3. First deploy:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   docker compose -f docker-compose.prod.yml exec api alembic upgrade head
   ```
4. **Git pull on the VPS** — the deploy script runs `git fetch` + `git reset --hard origin/main`. The server must authenticate to GitHub:
   - **Private repo:** add a [deploy key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) (read-only) to the repo and configure the matching private key on the VPS for `git fetch`, **or** use an HTTPS remote with a fine-grained PAT stored only on the server.
   - **Public repo:** HTTPS clone is enough.

5. Ensure the GitHub Actions SSH user can run Docker (root on this VPS is fine).

### What the workflow does

1. SSH into the VPS.
2. Run `scripts/deploy-vps.sh`: sync `main`, `docker compose build web api`, `up -d web api`.
3. Wait until API responds on `http://127.0.0.1:8000/` and the web container is running (fails the job on timeout).

## Manual deploy

On the VPS (or via SSH alias `hermes-vps` from your machine):

```bash
cd /root/projects/ppgcomdata
bash scripts/deploy-vps.sh
```

From your PC:

```bash
ssh hermes-vps 'cd /root/projects/ppgcomdata && bash scripts/deploy-vps.sh'
```

Force a clean Next.js build:

```bash
NO_CACHE_WEB=1 bash scripts/deploy-vps.sh
```

Full rebuild without cache:

```bash
NO_CACHE=1 bash scripts/deploy-vps.sh
```

## Backups diários (Postgres + uploads + `./data`)

O sistema de backup diário é feito via `systemd` e utiliza o script:
`/root/projects/ppgcomdata/scripts/backup-vps.sh`.

Ele gera uma pasta em:
`/root/backups/ppgcomdata/<YYYY-MM-DD_HH-mm-ss>/`

### O que é salvo

- Banco PostgreSQL: `postgres.dump` (formato `pg_dump --format=custom`)
- Volume Docker de uploads: `uploads.tar.gz` (volume `prod_uploads`)
- Pasta do projeto `./data`: `data.tar.gz`

### Retenção

Por padrão, mantém **14 dias** (`RETENTION_DAYS`, configurável via systemd).

### Timer systemd

Arquivos de referência (no repositório):
- `ops/ppgcomdata-backup.service`
- `ops/ppgcomdata-backup.timer`

Após atualizar o repositório na VPS, habilite com:

```bash
sudo systemctl daemon-reload
sudo cp ops/ppgcomdata-backup.service /etc/systemd/system/
sudo cp ops/ppgcomdata-backup.timer /etc/systemd/system/
sudo systemctl enable --now ppgcomdata-backup.timer
sudo systemctl list-timers | rg ppgcomdata-backup
```

## Local SSH config (optional)

Example `~/.ssh/config` entry (not used by GitHub Actions):

```
Host hermes-vps
  HostName <your-vps-ip>
  User root
  IdentityFile ~/.ssh/your_key
```

Actions use `VPS_HOST` / `VPS_USER` / `VPS_SSH_KEY` instead of the alias.
