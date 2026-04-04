# Setup da Fundacao

## Banco

O projeto usa `DATABASE_URL` e `DATABASE_ASYNC_URL` para PostgreSQL.
O arquivo `.env.example` traz uma configuração base.

## Fluxo recomendado

1. Instalar dependências
2. Subir PostgreSQL
3. Executar `alembic upgrade head`
4. Executar `python scripts/seed/minimal_seed.py`
5. Subir `uvicorn app.main:app --reload`

## Seed mínimo

O seed inicial cria:

- 12 signos
- 7 corpos celestes principais
- 12 casas
- 5 aspectos maiores
- 4 ângulos
- 1 escola editorial inicial

## Camada natal

Esta etapa adiciona:

- provider abstrato de efemérides
- provider analítico embutido
- adapter preparado para Swiss Ephemeris
- persistência de snapshots natais
- endpoints para criação e consulta de mapas

## Limites atuais

Ainda não entram nesta etapa:

- cálculo de alta precisão por padrão
- workers de produção
- painel admin funcional
- síntese interpretativa com LLM
