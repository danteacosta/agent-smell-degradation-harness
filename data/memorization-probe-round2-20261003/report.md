# Sonda de recuperação da regra — 3 de outubro de 2026 — rodada 2

Estado: `complete`. 60/60 pares requisito/modelo; 30 regras e 180 respostas previstas. Juízes qualificados: sim. Hashes verificados: 2342.

A sonda pergunta sobre o comportamento sem fornecer requisito, scaffold ou página. Recuperar a regra pode refletir familiaridade, inferência ou informação contida na pergunta; não demonstra contaminação de pré-treinamento.

O rótulo congelado `memorized=1` exige pelo menos duas de três respostas positivas, cada uma aceita pelos dois juízes. Os rótulos originais são preservados. Separadamente, uma decisão é inconclusiva quando respostas ausentes poderiam mudar esse limiar.

| Modelo | Pares observados | Rótulo congelado 1 | Recuperou | Não recuperou | Inconclusivo | Falha de geração | Julgamento sem decisão |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.6-luna | 30 | 8 | 8 | 22 | 0 | 0 | 0 |
| gpt-5.6-sol | 30 | 9 | 9 | 21 | 0 | 0 | 0 |

Pares sem resultado: 0. Eles não contam como recuperação nem como resultado negativo.

| Regra | Projeto | Modelo | Sim / não / desconhecido | Rótulo congelado | Diagnóstico |
|---|---|---|---|---:|---|
| rc-c6aa48543d73 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-c6aa48543d73 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-b49db6870ff5 | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-b49db6870ff5 | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-24946f42bfc2 | zulip | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-24946f42bfc2 | zulip | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-3c572449f134 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-3c572449f134 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-dfb84383fb89 | zulip | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-dfb84383fb89 | zulip | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-62e9d69be36f | zulip | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-62e9d69be36f | zulip | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-bf86d02f63c9 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-bf86d02f63c9 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-ade633af9c14 | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-ade633af9c14 | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-7b485b51412f | grist | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-7b485b51412f | grist | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-4aac15b7b503 | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-4aac15b7b503 | grist | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-3cd319371269 | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-3cd319371269 | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-f33b2bf870e9 | grist | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-f33b2bf870e9 | grist | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-c044ebec7fe1 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-c044ebec7fe1 | zulip | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-c30a4162188a | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-c30a4162188a | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-277279fd03a4 | zulip | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-277279fd03a4 | zulip | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-c5ed01f3769c | zulip | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-c5ed01f3769c | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-362ff82e3812 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-362ff82e3812 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-393307131fc8 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-393307131fc8 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-103dc930a420 | zulip | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-103dc930a420 | zulip | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-1590080019fb | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-1590080019fb | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-08dffa18a270 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-08dffa18a270 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-b7086f489030 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-b7086f489030 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-aac66a0af69a | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-aac66a0af69a | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-4200f1dac6a9 | zulip | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-4200f1dac6a9 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-adf56e244737 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-adf56e244737 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-f0b216964e6f | grist | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-f0b216964e6f | grist | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-fd348eb33246 | zulip | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-fd348eb33246 | zulip | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-6be0f3992b4b | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-6be0f3992b4b | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-cb144c65d898 | zulip | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-cb144c65d898 | zulip | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-b0a9c3fd790a | grist | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-b0a9c3fd790a | grist | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |

Este resultado é uma covariável exploratória. Não mede defeito E2E nem confirma H1 ou H2.

Public verification: `python3 verify.py --public .` from this folder.
