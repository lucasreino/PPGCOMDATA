# Backup diário + Google Drive

O PPGCOMDATA faz backup local diário na VPS e pode enviar cópias para o **Google Drive** via [rclone](https://rclone.org/drive/).

## O que é salvo

Cada execução cria uma pasta:

`/root/backups/ppgcomdata/<YYYY-MM-DD_HH-mm-ss>/`

| Arquivo | Conteúdo |
|---------|----------|
| `postgres.dump` | Banco PostgreSQL (`pg_dump` formato custom) |
| `uploads.tar.gz` | Volume Docker `prod_uploads` (PDFs enviados) |
| `data.tar.gz` | Pasta `./data` do projeto (XML Lattes, etc.) |
| `metadata.txt` | Informações do backup |

## Retenção

| Local | Padrão | Variável |
|-------|--------|----------|
| VPS | 14 dias | `RETENTION_DAYS` |
| Google Drive | 30 dias | `GDRIVE_RETENTION_DAYS` |

---

## Google Drive (recomendado: Service Account)

A forma mais estável para VPS **sem browser** é usar uma **Service Account** do Google Cloud e compartilhar uma pasta do Drive com ela.

### 1. Google Cloud — criar Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto (ex.: `ppgcomdata-backup`)
3. **APIs & Services → Library** → ative **Google Drive API**
4. **IAM & Admin → Service Accounts** → **Create service account**
   - Nome: `ppgcomdata-backup`
5. Na service account → **Keys → Add key → JSON**
   - Baixe o arquivo `.json` (guarde com segurança)

Anote o e-mail da service account, algo como:

`ppgcomdata-backup@seu-projeto.iam.gserviceaccount.com`

### 2. Google Drive — pasta compartilhada

1. No [Google Drive](https://drive.google.com/), crie uma pasta, ex.: `PPGCOMDATA-Backups`
2. **Compartilhar** com o e-mail da service account como **Editor**
3. Copie o **ID da pasta** da URL:

```
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      este é o root_folder_id
```

### 3. VPS — instalar rclone

```bash
curl https://rclone.org/install.sh | sudo bash
rclone version
```

### 4. VPS — configurar remote

```bash
sudo mkdir -p /root/.config/rclone
sudo chmod 700 /root/.config/rclone

# Copie o JSON da service account para a VPS (ex.: via scp)
# scp gdrive-sa.json hermes-vps:/root/.config/rclone/gdrive-sa.json
sudo chmod 600 /root/.config/rclone/gdrive-sa.json

sudo rclone config create ppgcomdata-gdrive drive \
  service_account_file /root/.config/rclone/gdrive-sa.json \
  root_folder_id SEU_FOLDER_ID_AQUI \
  scope drive
```

Teste:

```bash
sudo rclone lsd ppgcomdata-gdrive:
sudo rclone mkdir ppgcomdata-gdrive:backups
sudo rclone lsf ppgcomdata-gdrive:backups
```

### 5. VPS — habilitar upload no backup

```bash
sudo mkdir -p /etc/ppgcomdata
sudo cp /root/projects/ppgcomdata/ops/ppgcomdata-backup.env.example /etc/ppgcomdata/backup.env
sudo chmod 600 /etc/ppgcomdata/backup.env
sudo nano /etc/ppgcomdata/backup.env
```

Conteúdo mínimo:

```bash
RCLONE_REMOTE=ppgcomdata-gdrive:backups
RCLONE_CONFIG=/root/.config/rclone/rclone.conf
GDRIVE_RETENTION_DAYS=30
```

Atualize o systemd (após `git pull`):

```bash
sudo cp ops/ppgcomdata-backup.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Teste manual:

```bash
sudo systemctl start ppgcomdata-backup.service
sudo journalctl -u ppgcomdata-backup.service -n 50 --no-pager
```

Verifique no Google Drive a pasta `backups/<timestamp>/`.

---

## Alternativa: OAuth (conta pessoal)

Se preferir usar sua conta Google pessoal em vez de service account:

1. No seu PC (com browser): `rclone config` → escolha `drive` → siga o login OAuth
2. Copie `/root/.config/rclone/rclone.conf` (Linux) para a VPS:

```bash
scp ~/.config/rclone/rclone.conf hermes-vps:/root/.config/rclone/rclone.conf
ssh hermes-vps 'chmod 600 /root/.config/rclone/rclone.conf'
```

3. Use o nome do remote criado em `RCLONE_REMOTE` (ex.: `gdrive:PPGCOMDATA/backups`)

**Nota:** tokens OAuth podem expirar; service account é mais adequada para timer diário.

---

## Restaurar a partir de um backup

### Banco (postgres.dump)

```bash
BACKUP_DIR=/root/backups/ppgcomdata/2026-05-26_18-52-05

docker exec -i ppgcomdata-db-prod pg_restore -U postgres -d ppgcomdata --clean --if-exists \
  < "$BACKUP_DIR/postgres.dump"
```

### Uploads

```bash
docker run --rm \
  -v prod_uploads:/data \
  -v "$BACKUP_DIR:/backup:ro" \
  busybox:1.36 \
  sh -c 'cd /data && tar xzf /backup/uploads.tar.gz'
```

### Pasta data

```bash
cd /root/projects/ppgcomdata
tar xzf "$BACKUP_DIR/data.tar.gz"
```

### Baixar do Google Drive

```bash
rclone copy ppgcomdata-gdrive:backups/2026-05-26_18-52-05 /root/backups/restore/
```

---

## Timer systemd

```bash
sudo systemctl enable --now ppgcomdata-backup.timer
systemctl list-timers | grep ppgcomdata-backup
```

Horário padrão: **02:30** (fuso da VPS), com atraso aleatório de até 30 min.
