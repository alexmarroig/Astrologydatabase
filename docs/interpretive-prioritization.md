# Motor de Priorizacao Interpretativa

## Objetivo

Transformar fatores calculados do mapa natal em uma estrutura intermediaria pronta para a futura camada de sintese, sem ainda gerar texto longo final.

## O que entra

- planeta em signo
- planeta em casa
- aspecto planeta-planeta
- regencia por casa
- regencia por signo

## Persistencia

Tabelas adicionadas:

- `interpretive_matches`
- `interpretive_priority`
- `thematic_clusters`

## Logica de score

O motor combina quatro sinais principais:

- peso base editorial da `interpretation_rule`
- angularidade da casa envolvida
- exatidao do aspecto por `orb_deg`
- bonus para fatores ligados ao regente do ascendente

Depois disso:

1. agrega temas vindos de `interpretation_blocks`
2. aplica bonus por repeticao tematica
3. colapsa redundancias via `redundancy_group`
4. gera clusters tematicos para consumo posterior

## API

- `POST /api/v1/charts/{chart_id}/interpretive-priority`
- `GET /api/v1/charts/{chart_id}/interpretive-priority`

## Saida intermediaria

O snapshot retornado contem:

- `matches`: correspondencias fator-regra antes da consolidacao
- `priorities`: itens ordenados e deduplicados para sintese futura
- `clusters`: agrupamentos tematicos de alto nivel
