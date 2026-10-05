# Triagem histórica: 17 casos operativos

A revisão dos 40 candidatos terminou antes de qualquer geração A/H. O painel admitiu 19; a revisão das fontes colocou dois em quarentena. A coleta operativa tem 17 requisitos em oito projetos, com 12 casos de regra ausente e cinco de redação mais vaga. São 136 chamadas planejadas: A/H × dois modelos × duas repetições. Não há resultado novo de defeitos neste relatório.

## Painel e custódia

Astra e Sol foram os primários, com Terra 5.6 como desempate. Os três acertaram os cinco controles. A rodada concluída fez 104 chamadas: 45 por primário e 14 pelo desempate. Foram 31 acordos e nove desempates; os 40 pares primários tiveram votos válidos. Kappa foi 0,71098 para funcionalidade documentada e 0,83822 para estado da regra. Esses valores descrevem concordância, não correção nem validação humana.

As decisões foram: 13 yes/absent, seis yes/vaguer, cinco yes/same, cinco yes/different, dez no/absent e um no/vaguer. As quatro deleções e duas mudanças de página excluídas mecanicamente completam os 46 candidatos.

O recibo privado de 673 arquivos foi conferido integralmente. Seu SHA-256 é `6c266dcc67651c6c88dd08ecbf978013f6558b2de724c0040883c42f0fd92a54`. O resultado público é idêntico ao privado. As duas qualificações rejeitadas permanecem separadas, com seus motivos no protocolo. Nenhum voto foi refeito.

## Revisão antes do congelamento

A primeira construção ampliava a substituição para sentenças inteiras e apagava APIs/regras não alvo. Os H com redação mais vaga agora preservam C byte a byte e acrescentam a citação histórica em um parágrafo separado. Isso é uma reconstrução controlada; não é o documento histórico integral. Posição, duplicação e contexto moderno são limitações.

`panel-admission.json` preserva os 19 admitidos originalmente. `admission.json` registra o conjunto operativo e a revisão não cega de fontes, sem consultar resultados E2E. Os votos ficam intactos.

| Caso em quarentena | Motivo |
| --- | --- |
| Paperless custom field no value | C permite informar um valor; a citação antiga afirma incondicionalmente que nenhum valor será definido. A reconstrução contém instruções incompatíveis. |
| Nextcloud Mail favorites up | A fonte citada descreve Oldest/Newest, não favoritos na seção superior. Não sustenta a funcionalidade exigida pela admissão. |

As configs dessas duas reconstruções ficam em `data/historical-arm/quarantine/`, fora da pasta que o coletor percorre. Não contam como execuções, defeitos, empates ou desconhecidos.

## O que esta coleta responde

Com A coletado novamente junto com H, avaliaremos a perda da regra sob contexto moderno constante. Os 12 H=C são réplicas de omissão selecionadas pelo histórico; os cinco H=C+passagem antiga verificam se a formulação antiga recupera a obrigação. A análise deve separar essas construções. As repetições não são unidades independentes e tudo permanece exploratório; a auditoria humana continua pendente.
