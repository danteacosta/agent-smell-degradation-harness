# Replicação exploratória de omissão compartilhada com Claude 5.5

Autorização: em 06/10/2026, Dante pediu Sonnet 5.5 e Opus 5.5 após identificar que a bateria anterior usou versões 4.6. Este protocolo é publicado antes das novas gerações. A bateria 4.6 e o incidente Docker permanecem preservados; os resultados 5.5 serão publicados separadamente.

## Contraste e material

Replicar o desenho do #181/#184: 25 requisitos, oito projetos, três fontes (referência completa; pedido incompleto; pedido incompleto + código do mutante confirmado mostrado), duas suítes por fonte/modelo. São 300 slots novos, 150 por modelo, e 2.292 pares suíte/página previstos. Nenhuma implementação nova. Copiar por hash os 150 prompts, 191 páginas, mutantes selecionados, referências e ordem sorteada do pacote original. Cada modelo mantém a ordem interna; as chamadas alternam modelos. Não fornecer resultados, papéis ou oráculos ao testador.

IDs explícitos: `claude-sonnet-5-5` e `claude-opus-5-5`. Ambos responderam `SETUP_OK` na qualificação técnica por assinatura, com zero ferramentas/MCP e identidade coincidente. Congelar versão/hash do CLI e scripts. Adapter V2, esforço `low`, contexto isolado e as mesmas opções do estudo 4.6. Não é experimento para ranquear modelos: geração do código, seleção e páginas continuam reutilizadas.

## Cota e custódia

Aplicar desde o início a autorização de consumir a janela de cinco horas até zero, preservando **mais de 30% restante** nas demais janelas expostas. Sem API/uso extra/fallback de modelo. Toda chamada requer quota válida e janela futura; resposta com quota ausente/ambígua interrompe. Falhas e suítes inválidas permanecem tentadas e nunca são repetidas.

Cada etapa recebe diretório próprio de progresso, parada e recibo. Esgotamento confirmado da janela de cinco horas permite continuar apenas após o reset observado +60 segundos, com nova qualificação pública de quota, nenhum processo/lock anterior e integridade válida. Não repetir slot tentado, mesmo que falhou. Qualificações públicas não são slots de pesquisa. Qualquer outra parada exige aviso; não há retry automático. A avaliação Docker é executada uma vez, após completar geração, com controles qualificados antes do congelamento. Se Docker falhar, preservar o incidente e não repetir avaliação automaticamente.

## Desfechos e análise

Reutilizar sem alteração `mutation_adequacy.py` e `shared_omission_e2e.py`: escores com peso igual por requisito, MA1 (completa − incompleta) e MA2 (completa − incompleta+código mutante), bootstrap por projeto e teste bilateral exato por projeto. Manter suítes inválidas/não utilizáveis no denominador previsto. Publicar por modelo, com denominadores: falsos alarmes condicionais e incondicionais, referência correta × mutante mostrado, quietude no mutante e escore confirmado versus ingênuo. Discriminação por asserção é descritiva; não prova mecanismo sem auditoria humana.

Critério exploratório de cada contraste: intervalo de bootstrap acima de zero **e** p exato por projeto <0,05. Nenhuma mudança do desfecho, critérios, seleção, labels ou análise após observar resultados 5.5. Resultados anteriores são conhecidos: esta replicação não é confirmatória. H1 permanece exploratória, H2 não é testada, auditoria humana pendente.

## Verificação prevista

Regressões sem provedor real: nomes 5.5, prompts preservados, pacote novo, reserva semanal/modelo, esgotamento cinco horas, reset+60 e exclusão de tentativas anteriores. Conferir 300 pares modelo/slot únicos, hashes, recibos, relatórios reais versus placeholders. Publicar apenas agregados sanitizados e relatório, sem prompts, páginas, suítes ou respostas brutas. PR de resultados separado, sem merge automático.

Fontes oficiais consultadas em 06/10/2026: [modelos Claude](https://platform.claude.com/docs/en/models/overview), [Sonnet 5.5](https://www.anthropic.com/claude-sonnet-5-5), [Opus 5.5](https://www.anthropic.com/claude-opus-5-5).
