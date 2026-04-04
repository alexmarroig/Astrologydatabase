# Camada de Calculo Natal

## Objetivo

Persistir snapshots completos de mapas natais para consulta posterior e para uso futuro pela camada interpretativa.

## Provider de efemerides

O sistema expõe uma interface abstrata em `app/domain/ephemeris.py`.

Implementações atuais:

- `AnalyticalEphemerisProvider`
- `SwissEphemerisProvider`

O provider analítico é determinístico e serve para desenvolvimento e testes.
O adapter Swiss Ephemeris fica pronto para uso quando `pyswisseph` estiver instalado e `EPHEMERIS_PROVIDER=swisseph`.

## Snapshot persistido

Tabelas novas:

- `charts`
- `chart_positions`
- `chart_aspects`
- `chart_angles`
- `chart_house_cusps`

## Fluxo

1. Receber data, hora local, timezone offset e coordenadas
2. Converter para UTC
3. Calcular posições planetárias via provider
4. Calcular ângulos e casas
5. Derivar aspectos
6. Derivar regências
7. Persistir o snapshot completo

## Endpoints

- `POST /api/v1/charts/natal`
- `GET /api/v1/charts/{chart_id}`
- `GET /api/v1/charts/{chart_id}/factors`
