# Requisito antigo (t1) vs atual (tn): quem mudou, o que cada modelo fez, prints

Responde ao pedido do orientador: comparar, no histórico dos repositórios, o requisito com smell (t1) com o requisito sem smell (tn), rodar as LLMs nos dois e, quando o resultado diferir, mostrar quem fez a mudança e os prints.

**O que já foi feito.** A coleta do braço histórico (#166 a #168) é exatamente essa comparação, em 17 requisitos e 8 projetos:
- t1 é o texto antes do commit que escreveu a regra;
- tn é a documentação no fim da janela;
- foram rodados 2 modelos × 2 repetições em cada um.

Deu diferença em **8 de 17 requisitos**: 25 pares em que t1 violou a regra e tn não, e nenhum no sentido oposto. A tabela por requisito está em `data/historical-arm-results/v1/t1-tn/table.md`, com o commit, o autor e a data da mudança e o resultado de cada modelo e repetição. Ela foi gerada por `scripts/historical_evidence.py table`, a partir da coleta congelada, sem novas chamadas.

**Ressalvas para a reunião:**
- t1 é uma reconstrução controlada, não o documento antigo inteiro. Nos 12 casos de "regra ausente", t1 é o texto C; nos 5 de "passagem mais vaga", é C mais a frase antiga.
- tn é a documentação no fim da janela, não necessariamente o texto do commit seguinte.
- Das 25 pioras, 24 vêm de regra ausente e só 1 de passagem mais vaga.
- "Quem fez" aqui é o autor do commit que corrigiu a documentação. Um deles é um agente: `copilot-swe-agent[bot]`, no Nextcloud.

O piloto de setembro (10 requisitos, texto antigo contra corrigido, com prints em `data/e2e-decontamination-20260929/`) foi a primeira versão dessa comparação.

## Falta: os prints

Os prints do oráculo estão nos pacotes privados do Mac. O repositório só tem os hashes deles, dentro de `results.json`. Instrução para o Codex:

> No repositório agent-smell-degradation-harness, na branch `study/historical-t1-tn-evidence`:
> 1. Rode `python3 scripts/historical_evidence.py screenshots --packets "$HOME/Documents/GitHub/.private-research-evidence/historical-arm-v1"`. O comando copia só os prints dos 25 pares em que t1 e tn diferem e confere cada um contra o sha256 registrado. Se `missing` não vier vazio, informe e não substitua nenhum arquivo.
> 2. Rode `python3 scripts/historical_evidence.py gallery`.
> 3. Confira que os prints não mostram dados pessoais. As páginas são cenários sintéticos congelados, mas verifique.
> 4. Faça commit de `data/historical-arm-results/v1/t1-tn/screenshots/` e `gallery.html` nesta branch e faça push. Não faça merge.

A galeria (`gallery.html`) mostra, para cada requisito que mudou: a mudança, com o link do commit e o autor; a regra; e, em cada par que diferiu, os prints de t1 e tn lado a lado.
