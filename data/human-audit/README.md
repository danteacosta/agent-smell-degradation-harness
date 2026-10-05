# Auditoria humana cega dos painéis de LLM

Atende à decisão 2 da seção 8 do pré-registro: quem audita as decisões dos painéis.

`audit-sheet-20261005.xlsx` tem duas abas, além das instruções:

| Aba | Itens | Painel auditado | Pergunta |
| --- | ---: | --- | --- |
| `context_cue` | 46 | painel de `context_cue` v2 | a regra omitida pode ser inferida do texto do braço C? |
| `historico` | 40 | revisão da documentação antiga do braço H | a funcionalidade estava documentada antes? como a regra aparecia? |

**Cegamento.** A planilha mostra exatamente o que cada painel recebeu, em ordem embaralhada (semente 2026100504). As decisões dos modelos não estão nela. Quem auditar não deve abrir `data/context-cue/` nem `data/historical-arm/panel/` antes de terminar.

**Como preencher.** Preencha só as colunas amarelas, usando as listas suspensas, e salve com outro nome, por exemplo `audit-sheet-20261005-<iniciais>.xlsx`.

**Para comparar com o painel:**

```bash
python3 scripts/human_audit_sheet.py score data/human-audit/audit-sheet-20261005-<iniciais>.xlsx
```

O comando informa concordância, kappa e a lista de divergências. Respostas fora das listas e afirmações positivas sem citação literal são recusadas com o identificador do caso e a coluna a corrigir; linhas em branco não entram no cálculo. Na aba `historico`, informa também se cada divergência muda a admissão do caso. A comparação é com a decisão final do painel, antes da quarentena humana de dois casos feita no #167.

A planilha toma cerca de 2 a 3 horas. Se for preciso cortar, a aba `historico` é a que mais pesa: dela depende quais casos entraram no braço H.

## Triagem confirmatória: amostra aleatória de 20%

Atende ao compromisso da seção 3 do pré-registro: uma auditoria humana de 20% das decisões do painel, sorteadas ao acaso, antes de qualquer afirmação confirmatória.

`screening-audit-sheet-20261005.xlsx` tem 73 das 365 decisões das duas triagens confirmatórias de 05/10 (40 da reserva e 33 da janela 2024). As 2 sem decisão ficaram de fora. A amostra é estratificada por opção × projeto × decisão do painel, com alocação proporcional pelo maior resto, pelo menos um item por estrato e semente 2026100505.

O manifesto `screening-audit-sample-20261005.json` guarda só os IDs e a semente. O estrato revelaria a decisão do painel, e o `score` recalcula.

A planilha mostra o mesmo que o painel viu: projeto, arquivo e frases removidas e acrescentadas, com os mesmos três critérios. A decisão, o motivo e a regra do painel não aparecem. Quem auditar não deve abrir `data/llm-screening-confirmatory-*/` antes de terminar.

Para comparar com o painel:

```bash
python3 scripts/screening_audit_sample.py score data/human-audit/screening-audit-sheet-20261005-<iniciais>.xlsx
```

O comando informa:
- concordância e kappa de Cohen por opção (reserva e 2024), sem ponderação;
- dentro de cada decisão do painel, só a concordância, porque o rótulo do painel é constante ali e o kappa não informa nada;
- a concordância estimada para as 365 decisões, ponderando cada resposta pelo inverso da probabilidade de inclusão do seu estrato. A tabela de estratos, com tamanhos, sorteados, probabilidades e pesos, está em `screening-audit-design-20261005.json`, sem IDs. O erro-padrão reportado é um limite inferior, porque estratos com um único item não têm variância interna;
- as divergências e, quando os dois admitiram, a regra da pessoa ao lado da regra do painel, para ajudar na revisão de mapeamento.

As probabilidades de inclusão variam de 0,14 a 0,50: a garantia de pelo menos um item por estrato sobre-representa os estratos pequenos. Por isso as médias sem ponderação descrevem só a amostra.

A planilha leva cerca de 1 a 1,5 hora.
