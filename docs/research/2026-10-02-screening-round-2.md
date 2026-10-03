# Triagem, rodada 2: extensão do frame para o oitavo projeto

Status: coleta concluída em 3 de outubro de 2026. Ver [resultados da rodada 2](2026-10-03-screening-round2-results.md).

A rodada 1 admitiu regras de sete projetos; o pré-registro exige oito. Os outros cinco projetos da rodada 1 já tinham o frame inteiro triado, então uma nova amostra deles não muda a contagem. Por isso, o frame ganhou dois projetos, com a mesma janela (2025-01-01 a 2026-09-30) e os mesmos filtros. O desvio está registrado na seção 7 do pré-registro.

| Projeto | Fonte | Candidatos no frame | Amostra |
|---|---|---:|---:|
| Zulip | `help/`, `starlight_help/src/content/docs` (zulip/zulip @ 47d6b69) | 267 | 30 |
| Grist | `help/en/docs` (gristlabs/grist-help @ b047726) | 58 | 30 |

- Critério de escolha, antes de qualquer triagem: aplicações web open source ativas, com documentação de usuário em repositório git público.
- `functions.md` do Grist é a referência gerada de fórmulas (assinaturas e âncoras de busca; 244 dos 302 candidatos brutos) e foi excluída como as referências de API dos outros projetos.
- Penpot foi considerado e descartado: o guia do usuário está em templates `.njk`, fora das extensões previstas.
- Dois projetos, e não um, porque a taxa de admissão variou muito entre projetos na rodada 1 (cinco dos doze não tiveram admissões).

A amostra não tem pré-triagem do assistente. O painel, os controles, as instruções e a seed de ordem são os da rodada 1; `llm_screening_panel.py prepare` agora aceita `--screening`.

## Como rodar

```sh
bash scripts/run_llm_screening_round2.sh
# depois, a sonda dos admitidos desta rodada:
bash scripts/run_memorization_probe.sh "$HOME/Documents/GitHub/.private-research-evidence/llm-screening-round2-<data>"
```

São 18 chamadas de qualificação (seis controles para cada um dos três modelos), mais 120 votos primários e os desempates necessários. A sonda depende do número de admitidos (6 respostas por candidato, mais os julgamentos).

## Depois

A seleção final (`scripts/select_requirements.py select`, com os dois `--screening` e os dois `--frame`) só roda depois desta rodada e das decisões aprovadas.
