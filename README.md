# Astrologydatabase

Backend modular para um sistema astrologico profissional com FastAPI, SQLAlchemy, Alembic e PostgreSQL.

## O que existe agora

- API FastAPI modular em `app/`
- dominio de referencia astrologica e dominio editorial
- camada natal com calculo, snapshot persistido e consulta de fatores
- motor de priorizacao interpretativa com matches, prioridades e clusters tematicos
- migrations Alembic em `alembic/versions/`
- seed minimo em `scripts/seed/minimal_seed.py`
- testes de integracao em `tests/`
- estrutura reservada para `app/admin/` e `app/workers/`

## Setup rapido

1. Instale as dependencias:

```bash
pip install -r requirements.txt
```

2. Configure o banco usando `.env.example`.

3. Rode as migrations:

```bash
python -c "from alembic.config import main; main(argv=['upgrade', 'head'])"
```

4. Rode o seed minimo:

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
- `POST /api/v1/charts/{chart_id}/interpretive-priority`
- `GET /api/v1/charts/{chart_id}/interpretive-priority`

## Motor interpretativo

O motor de priorizacao usa o snapshot natal e as `interpretation_rules` publicadas para:

- selecionar regras relevantes
- combinar planeta em signo, planeta em casa, aspectos e regencias
- aplicar peso por angularidade, exatidao e regente do ascendente
- reforcar temas recorrentes
- persistir uma estrutura intermediaria para a futura camada de sintese

## Provider de efemerides

- `analytical` e o provider padrao para desenvolvimento e testes
- `swisseph` ja esta preparado por adapter opcional

Configure por ambiente:

- `EPHEMERIS_PROVIDER=analytical`
- `EPHEMERIS_PROVIDER=swisseph`

## Testes

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests -q -p pytest_asyncio.plugin
```
