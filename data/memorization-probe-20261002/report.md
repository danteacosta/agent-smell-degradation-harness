# Sonda de recuperação da regra — 2 de outubro de 2026

Estado: `complete`. 138/138 pares requisito/modelo; 69 regras e 414 respostas previstas. Juízes qualificados: sim. Hashes verificados: 5699.

A sonda pergunta sobre o comportamento sem fornecer requisito, scaffold ou página. Recuperar a regra pode refletir familiaridade, inferência ou informação contida na pergunta; não demonstra contaminação de pré-treinamento.

O rótulo congelado `memorized=1` exige pelo menos duas de três respostas positivas, cada uma aceita pelos dois juízes. Os rótulos originais são preservados. Separadamente, uma decisão é inconclusiva quando respostas ausentes poderiam mudar esse limiar.

| Modelo | Pares observados | Rótulo congelado 1 | Recuperou | Não recuperou | Inconclusivo | Falha de geração | Julgamento sem decisão |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.6-luna | 69 | 22 | 22 | 47 | 0 | 0 | 0 |
| gpt-5.6-sol | 69 | 31 | 31 | 38 | 0 | 0 | 0 |

Pares sem resultado: 0. Eles não contam como recuperação nem como resultado negativo.

| Regra | Projeto | Modelo | Sim / não / desconhecido | Rótulo congelado | Diagnóstico |
|---|---|---|---|---:|---|
| rc-882709afd891 | mattermost | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-882709afd891 | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-302720d6856b | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-302720d6856b | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-1986ea85580a | openproject | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-1986ea85580a | openproject | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-9c57cc2cca50 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-9c57cc2cca50 | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-ca08cec6ec87 | openproject | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-ca08cec6ec87 | openproject | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-84013890a131 | paperless | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-84013890a131 | paperless | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-e436521e462d | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-e436521e462d | openproject | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-458cc4cba31a | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-458cc4cba31a | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-d3faa64f9193 | nextcloud | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-d3faa64f9193 | nextcloud | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-c38fa60b1164 | nextcloud | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-c38fa60b1164 | nextcloud | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-0284c8781546 | mattermost | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-0284c8781546 | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-0ec1ac8f66bd | immich | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-0ec1ac8f66bd | immich | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-59d96b056593 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-59d96b056593 | wekan | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-0dde4b87ef72 | nextcloud | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-0dde4b87ef72 | nextcloud | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-57edf89f8e91 | wekan | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-57edf89f8e91 | wekan | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-de652e658b99 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-de652e658b99 | wekan | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-1114153d4704 | openproject | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-1114153d4704 | openproject | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-babbaaab4a5e | mattermost | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-babbaaab4a5e | mattermost | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-fbc75725d8ad | mattermost | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-fbc75725d8ad | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-4efba0098a79 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-4efba0098a79 | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-6b29ef8b44d8 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-6b29ef8b44d8 | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-4fa8e7483b1a | mattermost | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-4fa8e7483b1a | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-27e586be0e1e | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-27e586be0e1e | openproject | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-2c13970217ea | openproject | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-2c13970217ea | openproject | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-554bcd113361 | mattermost | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-554bcd113361 | mattermost | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-ebff8e70d1d7 | wekan | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-ebff8e70d1d7 | wekan | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-899c4d2472ad | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-899c4d2472ad | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-17b31565c57c | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-17b31565c57c | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-afa7beacea83 | immich | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-afa7beacea83 | immich | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-ab0227c1eb5b | nextcloud | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-ab0227c1eb5b | nextcloud | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-4041140f2b5d | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-4041140f2b5d | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-024102998dd2 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-024102998dd2 | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-3fbc295441e2 | mattermost | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-3fbc295441e2 | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-d595b3b1510f | nextcloud | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-d595b3b1510f | nextcloud | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-290b3ea47ca2 | wekan | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-290b3ea47ca2 | wekan | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-806442660eb5 | paperless | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-806442660eb5 | paperless | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-276016ee58a0 | openproject | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-276016ee58a0 | openproject | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-6fb3a96cddc0 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-6fb3a96cddc0 | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-6337ce108c4d | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-6337ce108c4d | openproject | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-086a9d210266 | paperless | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-086a9d210266 | paperless | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-b6b9f39b947a | mattermost | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-b6b9f39b947a | mattermost | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-60c42d4dd323 | mealie | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-60c42d4dd323 | mealie | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-15ed48fe86b0 | mattermost | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-15ed48fe86b0 | mattermost | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-c86728bbc029 | immich | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-c86728bbc029 | immich | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-e594b40135ff | nextcloud | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-e594b40135ff | nextcloud | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-9d801a70d5d2 | nextcloud | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-9d801a70d5d2 | nextcloud | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-476f8413ae2e | mattermost | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-476f8413ae2e | mattermost | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-969f81480445 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-969f81480445 | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-16b088247c39 | nextcloud | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-16b088247c39 | nextcloud | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-54a0e2c483c4 | mattermost | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-54a0e2c483c4 | mattermost | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-b6f382226c41 | immich | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-b6f382226c41 | immich | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |
| rc-106bac72c813 | mealie | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-106bac72c813 | mealie | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-aa2c82f86e08 | mattermost | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-aa2c82f86e08 | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-f3df2f6e5885 | wekan | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-f3df2f6e5885 | wekan | gpt-5.6-sol | 1 / 2 / 0 | 0 | not_recovered |
| rc-8b05adc7767e | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-8b05adc7767e | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-03a505847a99 | mattermost | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-03a505847a99 | mattermost | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-02df56f00b58 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-02df56f00b58 | openproject | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-88440629ecb6 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-88440629ecb6 | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-bd0b2995febc | mattermost | gpt-5.6-luna | 2 / 1 / 0 | 1 | recovered |
| rc-bd0b2995febc | mattermost | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-0c831f7cb825 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-0c831f7cb825 | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-035e8af08cd7 | paperless | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-035e8af08cd7 | paperless | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-946f02ef19b6 | nextcloud | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-946f02ef19b6 | nextcloud | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-49aaaf2e6630 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-49aaaf2e6630 | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-4da4940bc16c | mattermost | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-4da4940bc16c | mattermost | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-018ce2752c67 | openproject | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-018ce2752c67 | openproject | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-90d29a54a512 | wekan | gpt-5.6-luna | 0 / 3 / 0 | 0 | not_recovered |
| rc-90d29a54a512 | wekan | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-3d153b91ab4e | nextcloud | gpt-5.6-luna | 3 / 0 / 0 | 1 | recovered |
| rc-3d153b91ab4e | nextcloud | gpt-5.6-sol | 3 / 0 / 0 | 1 | recovered |
| rc-0f453b1f0a55 | mealie | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-0f453b1f0a55 | mealie | gpt-5.6-sol | 0 / 3 / 0 | 0 | not_recovered |
| rc-9e198862b86e | paperless | gpt-5.6-luna | 1 / 2 / 0 | 0 | not_recovered |
| rc-9e198862b86e | paperless | gpt-5.6-sol | 2 / 1 / 0 | 1 | recovered |

Este resultado é uma covariável exploratória. Não mede defeito E2E nem confirma H1 ou H2.

Public verification: `python3 verify.py --public .` from this folder.
