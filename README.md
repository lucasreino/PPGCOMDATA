# PPGCOMDATA

PPGCOMDATA é uma plataforma interna de gestão e análise de indicadores docentes voltada para Programas de Pós-Graduação em Comunicação (PPGCOM). O sistema é projetado para automatizar a consolidação de dados acadêmicos a partir de PDFs exportados do **Currículo Lattes**, processar as informações através de inteligência artificial com validação humana (human-in-the-loop), e gerar relatórios analíticos de fomento, projetos e produções.

---

## 📂 Estrutura do Repositório

Este projeto é organizado como um **Monorepo**:

```text
ppgcomdata/
├── apps/
│   ├── web/            # Frontend (Next.js 14, React, Tailwind CSS, shadcn/ui)
│   └── api/            # Backend (Python, FastAPI, SQLModel/SQLAlchemy, PyMuPDF)
├── database/           # Scripts SQL e controle de Migrations
├── docs/               # Manuais e documentação técnica do sistema
├── docker-compose.yml  # Configuração de containers para Ambiente Local
├── docker-compose.prod.yml # Configuração de containers para Produção (VPS)
└── README.md
```

---

## 🛠️ Pré-requisitos

Para executar o projeto localmente, você precisará de:

- **Docker** e **Docker Compose**
- **Git**
- Uma chave de API para o modelo de IA (configurável via `.env` do backend)

---

## 🚀 Como Iniciar (Ambiente Local)

### 1. Clonar o Repositório
```bash
git clone git@github.com:lucasreino/PPGCOMDATA.git
cd PPGCOMDATA
```

### 2. Configurar as Variáveis de Ambiente
Copie o arquivo `.env.example` da raiz (ou das respectivas pastas dos apps) e configure as variáveis adequadamente:
```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

### 3. Iniciar os Serviços com Docker Compose
```bash
docker compose up --build -d
```
Este comando iniciará:
- **Banco de Dados (PostgreSQL)** na porta `5432`
- **Backend API (FastAPI)** na porta `8000` (documentação Swagger disponível em `http://localhost:8000/docs`)
- **Frontend Web (Next.js)** na porta `3000` (acessível em `http://localhost:3000`)

### 4. Rodar as Migrations e Criar Usuário Administrador
Para criar o banco inicial e o primeiro usuário administrativo, execute:
```bash
# Executar as migrations do banco
docker compose exec api alembic upgrade head

# Criar o administrador padrão (informe a senha quando solicitado)
docker compose exec api python -m app.create_admin --email admin@ppgcom.edu --password "SuaSenhaSegura123"
```

---

## 🐳 Docker Services & Portas

| Serviço | Porta Local | Descrição |
| :--- | :--- | :--- |
| **Next.js Frontend** | `3000` | Painel de controle, upload de PDFs e relatórios |
| **FastAPI Backend** | `8000` | API Rest, processamento de PDFs e integração com LLM |
| **PostgreSQL DB** | `5432` | Banco relacional |

---

## 🚢 Deploy (VPS)

Produção na VPS com Docker Compose (`docker-compose.prod.yml`). Deploy automatizado via GitHub Actions ao fazer push em `main` (paths: `apps/web`, `apps/api`, compose de produção).

1. Configure os secrets no GitHub: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` (opcional: `VPS_PORT`).
2. Garanta que a VPS consiga `git fetch` do repositório (deploy key ou repo público).
3. Dispare manualmente em **Actions → Deploy to VPS** se precisar de rebuild sem cache.

Detalhes, checklist de primeira instalação e deploy manual: **[DEPLOY.md](DEPLOY.md)**.

```bash
# Fallback manual na VPS
bash scripts/deploy-vps.sh
```

---

## 📝 Licença

Este projeto é de uso restrito e confidencial para fins institucionais de pós-graduação.

---

## Testes (API)

```bash
cd apps/api
pip install -r requirements.txt
pytest
```
