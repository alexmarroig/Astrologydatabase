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

## Contrato editorial engine-ready

Para a expansao helenistica, o conteudo interpretativo novo passa a existir primeiro em dataset estruturado:

- `data/hellenistic/planet_in_sign.py`

Cada item usa:

- `subject_1_type` / `subject_1_id`
- `subject_2_type` / `subject_2_id`
- `system`
- `base_weight`
- `core_statement`
- `manifestation`
- `risk_expression`
- `modifiers_json`

O validador em `scripts/seed/contracts.py` garante:

- campos obrigatorios
- identificadores em lowercase
- shape computavel de `modifiers_json`
- ranges padronizados de `weight_delta`

O loader em `scripts/seed/full_seed.py` faz a ponte desse contrato novo para o schema relacional atual.
