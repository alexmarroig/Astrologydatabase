# Setup da Fundacao

## Banco

O projeto usa `DATABASE_URL` e `DATABASE_ASYNC_URL` para PostgreSQL.
O arquivo `.env.example` traz uma configuracao base.

## Fluxo recomendado

1. Instalar dependencias
2. Subir PostgreSQL
3. Executar `alembic upgrade head`
4. Executar `python scripts/seed/minimal_seed.py`
5. Subir `uvicorn app.main:app --reload`

## Seed minimo

O seed inicial cria:

- 12 signos
- 7 corpos celestes principais
- 12 casas
- 5 aspectos maiores
- 4 angulos
- 1 escola editorial inicial

## Camada natal

Esta etapa adiciona:

- provider abstrato de efemerides
- provider analitico embutido
- adapter preparado para Swiss Ephemeris
- persistencia de snapshots natais
- endpoints para criacao e consulta de mapas

## Motor interpretativo

Esta etapa adiciona:

- priorizacao intermediaria baseada em regras publicadas
- persistencia de `interpretive_matches`
- persistencia de `interpretive_priority`
- persistencia de `thematic_clusters`
- endpoints para calcular e consultar o snapshot interpretativo

## Limites atuais

Ainda nao entram nesta etapa:

- calculo de alta precisao por padrao
- workers de producao
- painel admin funcional
- sintese interpretativa com LLM
