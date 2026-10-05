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
