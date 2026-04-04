# Astrologydatabase

Backend modular para um sistema astrológico profissional com FastAPI, SQLAlchemy, Alembic e PostgreSQL.

## O que existe agora

- API FastAPI modular em `app/`
- domínio de referência astrológica e domínio editorial
- camada natal com cálculo, snapshot persistido e consulta de fatores
- migrations Alembic em `alembic/versions/`
- seed mínimo em `scripts/seed/minimal_seed.py`
- testes de integração em `tests/`
- estrutura reservada para `app/admin/` e `app/workers/`

## Setup rápido

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Configure o banco usando `.env.example`.

3. Rode as migrations:

```bash
python -c "from alembic.config import main; main(argv=['upgrade', 'head'])"
```

4. Rode o seed mínimo:

```bash
python scripts/seed/minimal_seed.py
```

5. Suba a API:

```bash
uvicorn app.main:app --reload
```

## Endpoints natais

- `POST /api/v1/charts/natal`
- `GET /api/v1/charts/{chart_id}`
- `GET /api/v1/charts/{chart_id}/factors`

## Provider de efemérides

- `analytical` é o provider padrão para desenvolvimento e testes
- `swisseph` já está preparado por adapter opcional

Configure por ambiente:

- `EPHEMERIS_PROVIDER=analytical`
- `EPHEMERIS_PROVIDER=swisseph`

## Testes

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests -q -p pytest_asyncio.plugin
```
