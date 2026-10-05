# t1 (antes do commit) vs tn (documentação no fim da janela)

8 de 17 requisitos deram resultado diferente entre t1 e tn em pelo menos um par modelo × repetição. Fonte: coleta congelada `data/historical-arm-results/v1`; sem novas chamadas.

| Requisito | Mudança (autor, data) | t1 | luna r1/r2 | sol r1/r2 |
| --- | --- | --- | --- | --- |
| grist-page-default-collapse | [537c682145](https://github.com/gristlabs/grist-help/commit/537c682145f0450c16f780ac9ce7ff7834cce587), Natalie Misasi, 2025-10-02 | regra ausente | t1 pior / t1 pior | t1 pior / t1 pior |
| grist-suggestions-open-copy | [af6962bf5b](https://github.com/gristlabs/grist-help/commit/af6962bf5b4316f17a95e0e577c381e6ec1ddd9b), nbush, 2026-01-30 | passagem mais vaga | ambos ok / ambos ok | ambos ok / ambos ok |
| immich-library-single-owner | [eee793bfe4](https://github.com/immich-app/immich/commit/eee793bfe4a2e48aea595ad7563bfaf038dd2cd5), Jason Rasmussen, 2025-10-08 | regra ausente | t1 pior / t1 pior | t1 pior / t1 pior |
| immich-m2t-upload | [fcd372238f](https://github.com/immich-app/immich/commit/fcd372238fac7db3908387a0b3b4c953179bb99e), Mert, 2025-01-03 | regra ausente | t1 pior / t1 pior | t1 pior / t1 pior |
| mattermost-anonymous-team-url | [840fc4b8f5](https://github.com/mattermost/docs/commit/840fc4b8f580d1c369945c827678a896b1389049), Combs7th, 2026-04-15 | regra ausente | t1 pior / t1 pior | ambos ok / t1 pior |
| mattermost-timezone-default-automatic | [34180cef60](https://github.com/mattermost/docs/commit/34180cef60dbe502477d4b0d353b07192edf24e2), Carrie Warner (Mattermost), 2025-08-20 | regra ausente | ambos ok / ambos ok | ambos ok / ambos ok |
| nextcloud-device-password-once | [a806a064bc](https://github.com/nextcloud/documentation/commit/a806a064bc8adebbdaf8525c387543b55d4b00db), copilot-swe-agent[bot], 2026-05-04 | passagem mais vaga | ambos falham / t1 pior | ambos ok / ambos ok |
| openproject-filter-text-autoupdate | [db54165614](https://github.com/opf/openproject/commit/db54165614946caf2436a5cb2d601c898412326b), Maya Berdygylyjova, 2025-04-11 | passagem mais vaga | ambos falham / ambos falham | ambos falham / ambos falham |
| openproject-invite-permission-basis | [b09683d857](https://github.com/opf/openproject/commit/b09683d8576f827834da9e3391a40cb807a0dc8c), Maya Berdygylyjova, 2025-12-23 | regra ausente | ambos falham / desconhecido | ambos falham / desconhecido |
| paperless-doc-title-placeholder | [63c0e2f72b](https://github.com/paperless-ngx/paperless-ngx/commit/63c0e2f72b53ca2d38851930a4bcd1d5c8b52321), shamoon, 2026-02-03 | regra ausente | ambos falham / ambos falham | t1 pior / ambos falham |
| paperless-superuser-grant | [41bcc12cc2](https://github.com/paperless-ngx/paperless-ngx/commit/41bcc12cc2ae01d99957518a9b88126e16bb7c71), shamoon, 2025-01-20 | regra ausente | t1 pior / t1 pior | t1 pior / t1 pior |
| wekan-field-order-independent | [15b2b6c533](https://github.com/wekan/wekan/commit/15b2b6c5339979341d8237aa592ae37a5fd0607d), Lauri Ojansivu, 2026-09-11 | regra ausente | ambos ok / ambos ok | ambos ok / ambos ok |
| wekan-swimlane-below-default | [5ed4268a61](https://github.com/wekan/wekan/commit/5ed4268a61b19898c671b64b1ead786494f171b9), Lauri Ojansivu, 2026-09-27 | regra ausente | t1 pior / t1 pior | t1 pior / t1 pior |
| wekan-sync-local-edits | [b254b7d3af](https://github.com/wekan/wekan/commit/b254b7d3afb112d2e72f36f3fc8eb7a4a998ae23), Lauri Ojansivu, 2026-09-27 | passagem mais vaga | ambos ok / ambos ok | ambos ok / ambos ok |
| wekan-week-number-immediate | [e217f1215a](https://github.com/wekan/wekan/commit/e217f1215a0f99271f1f752f841fe412fb0c3339), Lauri Ojansivu, 2026-09-23 | regra ausente | ambos ok / ambos ok | ambos ok / ambos ok |
| zulip-gif-picker-disabled | [a31cd65175](https://github.com/zulip/zulip/commit/a31cd65175c5a219d83df9758829cb6f86cf24fa), Alya Abbott, 2026-03-24 | passagem mais vaga | ambos ok / ambos ok | ambos ok / ambos ok |
| zulip-reverse-linkifier-paste | [3ca12e7224](https://github.com/zulip/zulip/commit/3ca12e7224e7158d866f3d24f52ce877749fb742), Shubham Padia, 2026-03-02 | regra ausente | desconhecido / ambos falham | ambos falham / ambos falham |

t1 pior = a regra foi seguida com o texto tn e violada com o texto t1, no mesmo modelo e repetição.
Prints: `data/historical-arm-results/v1/t1-tn/screenshots/` (copiados dos pacotes privados com hash conferido) e a galeria `gallery.html`.
