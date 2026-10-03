# Coleta dos 46 requisitos: primeiro resultado E2E

Status em 03/10: 1 dos 46 requisitos terminou geração e avaliação. A coleta dos demais continua na ordem congelada. Este relatório não antecipa os resultados restantes.

Após o merge do #152, os 552 prompts foram congelados antes da primeira chamada: 46 requisitos × A/B/C × Luna/Sol × duas repetições. Duas chamadas separadas verificaram acesso aos modelos pela assinatura do Codex e não integram os 552 slots. Os modelos solicitados são `gpt-5.6-luna` e `gpt-5.6-sol`; a CLI não expõe o snapshot efetivo. Não houve retry, reparo ou alteração dos prompts após observar respostas.

## Senha de dispositivo: Nextcloud

A obrigação é exibir a senha somente na criação, sem permitir consultá-la depois. A contém a obrigação; B a reescreve; C remove seu trecho. A página é uma reconstrução sintética baseada na documentação pública congelada, não a aplicação Nextcloud completa.

| Modelo | A, completo | B, reescrito | C, omissão |
| --- | --- | --- | --- |
| Luna | 2 sucessos | 1 sucesso, 1 defeito-alvo | 2 defeitos-alvo |
| Sol | 2 sucessos | 2 sucessos | 2 sucessos |

São 12 execuções avaliáveis, sem falha de origem/navegador e sem caso inconclusivo. Nas quatro comparações A/C pareadas por modelo e repetição, há duas degradações com omissão no Luna e dois empates em sucesso no Sol. Todas pertencem a **um requisito**; não representam quatro requisitos independentes.

As duas páginas C do Luna permitiram revelar a senha posteriormente, embora tenham criado/exibido a senha e listado os dispositivos corretamente. O Sol cumpriu a regra nas duas páginas C. O texto C ainda informa que o Nextcloud não salva a senha em texto simples; as duas implementações Sol-C invocam essa informação para recusar a consulta. Essa é uma pista concreta de contexto, já registrada antes da coleta, mas não identifica causalmente a origem do comportamento nem comprova memorização. A falha em B do Luna também foi preservada: a reescrita completa não garantiu cumprimento em todas as execuções.

## Evidência e limites

[Pacote público](../../data/selection-abc-results/20261003/nextcloud-device-password-once/) inclui os 12 prompts congelados, runtimes, HTMLs gerados, relatórios, 24 prints e hashes. As capturas brutas do provedor permanecem privadas. O recibo original registra sua custódia; o recibo de publicação cobre apenas os arquivos públicos e não promete disponibilidade dos arquivos privados. Os nomes e senhas das fixtures são dados sintéticos de teste.

A revisão de integração foi não cega e teve exposição prévia à sonda. A coleta permanece exploratória, com `confirmatory_eligible: false`. A auditoria humana e os rótulos ordinais independentes continuam pendentes. Este resultado fornece evidência local de degradação em um modelo e cumprimento observado em C no outro; não confirma H1 geral nem testa H2.

## Continuidade

O segundo caso é `grist-suggestions-open-copy`. Os 45 casos ainda sem avaliação concluída não entram neste placar. Falhas, recusas e slots não tentados serão contabilizados separadamente; os resultados anteriores não serão substituídos.
