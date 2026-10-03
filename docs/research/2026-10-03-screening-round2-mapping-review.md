# Revisão cega de mappings da rodada 2 — proposta pendente

Status: revisão por LLM, conferida por outra execução da assistência; somente leitura, sem aprovação, exclusão, remapping, seleção ou congelamento de E2Es.

Registrado em UTC: 2026-10-03T16:16:07.986965+00:00

## Custódia e cegamento

Entradas: somente resultados da TRIAGEM e seu pacote frozen; complementarmente, o frame de triagem já existente para identificar commit/data e mudanças relacionadas. Não foi aberta a sonda, seus arquivos, chamadas, respostas, julgamentos ou resultados. Nenhum resultado experimental orientou esta revisão. Nenhum arquivo do repositório foi modificado.

- results.json SHA-256: `efd715003c462e0af5cdc149f23ba98744a4bea051751eb6a2e5be85f800a4d6`
- frozen/manifest.json SHA-256: `98e747aa02b1c383c3d4cb2ec42fa24172902aac6712a31eea5cf278aa329c56`
- Resultados públicos: [triagem da rodada 2](../../data/llm-screening-round2-20261003/results.json).
- Frame complementar: [candidatos de Zulip e Grist](../../data/requirement-sampling/screening-ext-20261002.json).
- Frame SHA-256: `c18866299e07cd91707ff230c0b71ef3f9c14c9737311ef41a182ec3fe8565e8`

## Critérios e limites

**V1:** a regra precisa estar expressa no texto que efetivamente comporá A. Para uma adição, o delta comprova presença no snapshot pós-commit, não na documentação atual posterior. Para uma remoção, comprova presença no snapshot anterior, não no posterior. Não existe A final congelado para esses 30 candidatos neste pacote; portanto, nenhuma revisão abaixo certifica A final ou documentação atual. Mudanças relacionadas citadas são material de fonte, não outcomes.

**V2:** a regra precisa descrever comportamento observável/obrigação testável, não somente presença, rótulo ou localização de controle. Uma observação também não pode reduzir configurabilidade funcional à simples presença de um setting.

Compararam-se regra congelada, trechos antes/depois, observações congeladas e demais votos favoráveis. Diferenças meramente estilísticas não são flags. Flags são itens de revisão, jamais decisões. Os textos abaixo são os trechos extraídos congelados, preservados exatamente como strings; não substituem a página integral nem expansão de includes.

Cobertura: 30/30 elegíveis revisados. 15 candidatos com divergência concreta ou questão V1/V2; 7 elegíveis têm apenas texto removido. Os demais não apresentaram divergência concreta nos recortes examinados, sem implicar aprovação.

## Revisão por candidato

### rc-c6aa48543d73 — zulip

Fonte do frame: `71da6f261c43e2ebe3ccaacf5e32acfd3ea78f5e`, `help/require-topics.md`, data `2025-02-26`.

**Regra congelada:** When administrators require topics in channel messages, users cannot send channel messages to the “general chat” topic.

**Antes — frases removidas (exatas):**

```text
If a user sends a message without a topic, the message's topic is displayed as (no topic) .
```

```text
Administrators can configure whether channel messages must have a specified topic.
```

**Depois — frases adicionadas (exatas):**

```text
{!general-chat-intro.md!}  Administrators can require topics in channel messages to disable the “*general chat*” topic.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: When administrators require topics in channel messages, users cannot send channel messages to the “general chat” topic.
- `gpt-6-sol`: When an administrator requires topics in channel messages, the “general chat” topic is unavailable.

**Observação positiva congelada:** With topics required, the interface prevents sending a channel message to “general chat”.

**Observação negativa congelada:** With topics required, a user successfully sends a channel message to “general chat”.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-b49db6870ff5 — grist

Fonte do frame: `b5e6d897fc1f0a8ef5194d5067766a950ca10650`, `help/en/docs/document-tutorials.md`, data `2025-06-02`.

**Regra congelada:** After a user closes their document fork, visiting the document's Direct URL automatically redirects them to their saved fork.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
If you close out of your fork of the document, you can always return to your fork by visiting the Direct URL — Grist will redirect you to your saved fork automatically.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: After a user closes their document fork, visiting the document's Direct URL automatically redirects them to their saved fork.
- `gpt-6-sol`: When a user revisits the Direct URL after closing their document fork, Grist redirects them to their saved fork.

**Observação positiva congelada:** The user visits the Direct URL after closing their fork and sees their saved fork open automatically.

**Observação negativa congelada:** The user visits the Direct URL after closing their fork and is not automatically taken to their saved fork.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-24946f42bfc2 — zulip

Fonte do frame: `cb1731566eeaf678155e8ae3cd953a5230140810`, `help/user-groups.md`, data `2025-03-17`.

**Regra congelada:** A user may join a user group using its plus icon only if they have permission to join it.

**Antes — frases removidas (exatas):**

```text
Click the plus ( ) icon to the left of a user group to join the group.
```

**Depois — frases adicionadas (exatas):**

```text
Click the plus (<img src="/static/images/help/desktop-web-plus-icon.svg" alt="plus" class="help-center-icon"/>) icon to the left of a user group to join the group, if you have permission to do so.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: A user may join a user group using its plus icon only if they have permission to join it.
- `gpt-6-sol`: A user can join a user group by clicking its plus icon only if they have permission to join it.

**Observação positiva congelada:** A user without permission cannot join the group through its plus icon.

**Observação negativa congelada:** A user without permission joins the group through its plus icon.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-3c572449f134 — zulip

Fonte do frame: `d6af4acb35062c0c43569a8c2fe2b7e7062da7d7`, `help/direct-messages.md`, data `2025-07-29`.

**Regra congelada:** Typing a user's name in the search box offers a suggestion for direct messages with that user.

**Antes — frases removidas (exatas):**

```text
Click the search (<i class="search_icon zulip-icon zulip-icon-search"> ) icon in the top bar to open the search box .
```

```text
Start typing a user's name.
```

```text
You'll be able to select DMs with that user from the list of suggestions.
```

```text
1. *(optional)* Continue to add users via the search box for a group DM conversation.  !!! tip ""  You can also type dm-including in the search box to find all 1:1 and group DM conversations that include a particular user.
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Typing a user's name in the search box offers a suggestion for direct messages with that user.
- `gpt-6-sol`: Searching for `dm-including` followed by a user finds all one-to-one and group DM conversations that include that user.

**Observação positiva congelada:** The suggestions include an option for direct messages with the named user.

**Observação negativa congelada:** The suggestions omit an option for direct messages with the named user.

**Revisão: Revisão V1 e unidade-alvo.** A regra congelada está somente nas frases removidas. Astra escolhe sugestão ao digitar um nome; Sol escolhe a consulta dm-including para conversas 1:1 e em grupo. São ações/resultados diferentes, não paráfrases. Não há regra adicionada que sustente a obrigação no texto pós-commit mostrado.

### rc-dfb84383fb89 — zulip

Fonte do frame: `bde295806c9952f70a2b58317b58f7e31c59faf7`, `help/include/unsubscribe-user-from-channel.md`, data `2025-07-21`.

**Regra congelada:** Any user can unsubscribe themselves from a channel they belong to.

**Antes — frases removidas (exatas):**

```text
{!admin-only.md!}  Anyone can always unsubscribe themselves from a channel .
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Any user can unsubscribe themselves from a channel they belong to.
- `gpt-6-sol`: A user can unsubscribe themselves from any channel.

**Observação positiva congelada:** A non-admin user unsubscribes from a channel and sees that they are no longer subscribed.

**Observação negativa congelada:** A non-admin user is prevented from unsubscribing from a channel they belong to.

**Revisão: Revisão V1.** A obrigação de auto-desinscrição é observável e está explícita em Anyone can always unsubscribe themselves, mas somente no texto removido. A vs C depende da decisão sobre usar documentação anterior ou atual; o diff não prova sua presença no documento atual completo.

### rc-62e9d69be36f — zulip

Fonte do frame: `befe49c293c7cc490d4dfb94b387411591d1f114`, `help/configure-who-can-administer-a-channel.md`, data `2025-02-12`.

**Regra congelada:** A user with permission to administer a private channel must also subscribe to that channel before they can subscribe other users to it.

**Antes — frases removidas (exatas):**

```text
If you have permission to administer a public or web-public channel, you can:  See and modify the channel's name and description .
```

```text
Subscribe and unsubscribe users.
```

```text
Modify the channel's permissions settings, including settings that control who can see messages in the channel (public vs. private, shared history vs. protected history).
```

```text
For private channels, you additionally need to be a subscriber in order to subscribe users or change channel permissions.
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: A user with permission to administer a private channel must also subscribe to that channel before they can subscribe other users to it.
- `gpt-6-sol`: An administrator of a private channel must be subscribed to it before they can change its permissions.

**Observação positiva congelada:** An administrator who is not subscribed to the private channel cannot add subscribers through the web interface.

**Observação negativa congelada:** An administrator who is not subscribed to the private channel successfully adds a subscriber through the web interface.

**Revisão: Revisão V1 e unidade-alvo.** A frase removida exige inscrição para duas ações distintas: subscribe users e change channel permissions. A regra congelada escolhe a primeira; Sol escolhe a segunda. Ambas têm suporte no texto anterior, mas não são a mesma obrigação. Nenhum texto adicionado preserva a regra neste delta.

### rc-bf86d02f63c9 — zulip

Fonte do frame: `b742ab18f90d8a0320f6b14be311e0f351903eb6`, `starlight_help/src/content/docs/emoji-and-emoticons.mdx`, data `2025-10-01`.

**Regra congelada:** When Google blobs is selected, emoji released after 2017 must display in the modern Google style.

**Antes — frases removidas (exatas):**

```text
Google blobs is an old style of Google emoji that has not been maintained by Google since 2017, when they switched to a more modern style.
```

```text
Zulip allows you to still use blob emoji, but any new emoji that have been released since 2017 will be displayed in the modern Google style.
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: When Google blobs is selected, emoji released after 2017 must display in the modern Google style.
- `gpt-6-sol`: When the Google blobs emoji style is selected, emoji released after 2017 display in the modern Google style.

**Observação positiva congelada:** An emoji released after 2017 appears in the modern Google style while Google blobs is selected.

**Observação negativa congelada:** An emoji released after 2017 appears in blob style or fails to display while Google blobs is selected.

**Revisão: Revisão V1.** O estilo moderno para emojis posteriores a 2017 é expresso e observável, mas apenas nas frases removidas. Não foi demonstrado que esse trecho estará no futuro braço A de documentação atual.

### rc-ade633af9c14 — grist

Fonte do frame: `af6962bf5b4316f17a95e0e577c381e6ec1ddd9b`, `help/en/docs/sharing.md`, data `2026-01-30`.

**Regra congelada:** When suggestions are enabled, opening a document automatically opens a copy for both signed-in and signed-out users.

**Antes — frases removidas (exatas):**

```text
A user makes changes in a personal copy without modifying the original document, then submits these suggestions to be reviewed by the document owner prior to integration.
```

**Depois — frases adicionadas (exatas):**

```text
With suggestions enabled, users (signed-in or not) automatically open a copy of a document.
```

```text
They make edits to this copy without modifying the original, and then submit these suggestions to be reviewed by the document Owner prior to integration.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: When suggestions are enabled, opening a document automatically opens a copy for both signed-in and signed-out users.
- `gpt-6-sol`: When suggestions are enabled, opening a document automatically opens a copy for editing, including for users who are not signed in.

**Observação positiva congelada:** A user opening the document with suggestions enabled sees a copy, whether signed in or signed out.

**Observação negativa congelada:** A user opening the document with suggestions enabled sees the original instead of a copy.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-7b485b51412f — grist

Fonte do frame: `537c682145f0450c16f780ac9ce7ff7834cce587`, `help/en/docs/page-widgets.md`, data `2025-10-02`.

**Regra congelada:** After a user selects 'Set default: Collapse' for a parent page, its nested pages must be collapsed when the document is reopened.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
Pages can be rearranged by clicking the two verticle bars to the right of the page name then dragging to a new position.
```

```text
A green line will appear to show where the page will be placed.
```

```text
A green box will appear to show when a page will be nested under another.  ! rearrange_pages * {: .screenshot-half }  By default, nested pages will be expanded when a document is opened.
```

```text
You can change the default state by clicking the three-dot icon to the right of the parent page and selecting 'Set default: Collapse'.  ! page-set-default-state * {: .screenshot-half }
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: After a user selects 'Set default: Collapse' for a parent page, its nested pages must be collapsed when the document is reopened.
- `gpt-6-sol`: While a user drags a page to rearrange it, a green line shows where the page will be placed.

**Observação positiva congelada:** When the document is reopened, the parent page's nested pages are hidden in the page list.

**Observação negativa congelada:** When the document is reopened, the parent page's nested pages are expanded in the page list.

**Revisão: Revisão da unidade-alvo.** As frases adicionadas contêm tanto feedback verde durante drag quanto default de collapse ao reabrir. A regra congelada de Astra escolhe persistência do default; Sol escolhe a linha verde durante drag. São duas obrigações distintas sustentadas pela fonte. O consenso de admissão não é consenso sobre qual delas será manipulada; não há indicação de que a regra congelada esteja ausente do delta.

### rc-4aac15b7b503 — grist

Fonte do frame: `bcdbeb35aca412455369ac498fee23bdc1009a63`, `help/en/docs/keyboard-shortcuts.md`, data `2026-05-29`.

**Regra congelada:** Pressing Shift+F10 in the grid opens the context menu.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
*⌃* *Enter* , *↑* *F10* | *Menu* , *Shift* + *F10* | Open the context menu | *↑* *⌃* *Enter* , *⌃* *↑* *F10* | *Ctrl* + *Menu* , *Ctrl* +*Shift* + *F10* | Open the current column menu | *⌥* *⌃* *Enter* , *⌥* *↑* *F10* | *Alt* + *Menu* , *Alt* +*Shift* + *10* | Open the current row menu |
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Pressing Shift+F10 in the grid opens the context menu.
- `gpt-6-luna`: In the web interface, pressing the listed shortcut for the current cell opens its context menu.

**Observação positiva congelada:** The context menu appears after the user presses Shift+F10 in the grid.

**Observação negativa congelada:** No context menu appears after the user presses Shift+F10 in the grid.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-3cd319371269 — grist

Fonte do frame: `7112b1767aac275712073fbcf91756d33f0c952a`, `help/en/docs/on-demand-tables.md`, data `2025-05-05`.

**Regra congelada:** Users cannot enable On-Demand Tables in new Grist documents.

**Antes — frases removidas (exatas):**

```text
!!! warning "On-demand tables are an experimental feature" The design of on-demand tables may change.
```

```text
For example, configuration options may be added, or aspects of the behavior of on-demand tables may be changed entirely.
```

**Depois — frases adicionadas (exatas):**

```text
!!! warning "⚠️ Deprecated Feature" On-Demand Tables have been deprecated and are no longer supported in new Grist documents.
```

```text
Existing documents that use On-Demand Tables will continue to function.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-luna`: Existing Grist documents that use On-Demand Tables continue to function.
- `gpt-6-sol`: Users cannot enable On-Demand Tables in new Grist documents.

**Observação positiva congelada:** A new document offers no way to enable On-Demand Tables.

**Observação negativa congelada:** A user can enable On-Demand Tables in a new document.

**Revisão: Revisão V1, força da regra e unidade-alvo.** A fonte acrescenta no longer supported in new Grist documents e Existing documents ... continue to function. Sol congela impossibilidade de habilitar em documentos novos; Luna escolhe funcionamento de documentos existentes. São população, ação e resultado diferentes. Unsupported não especifica sozinho que a UI impede habilitar, logo o pass/fail congelado exige um mecanismo mais forte que a frase. Outro candidato do mesmo arquivo/data remove as duas frases; é necessária verificação da versão/topologia antes de afirmar presença no A atual, sem inferir ordem intradiária apenas pela data.

**Mudança relacionada:** `rc-37c8b91a246a`, commit `df41eb0a54eefdbf99ad66a87bc3dcf264613bf9`, data `2025-05-05`, arquivo `help/en/docs/on-demand-tables.md`.

Frases removidas exatas:

```text
On-Demand Tables have been deprecated and are no longer supported in new Grist documents.
```

```text
Existing documents that use On-Demand Tables will continue to function.
```

Frases adicionadas exatas:

```text
On-Demand Tables have been deprecated due to lack of functionality and usability concerns.
```

### rc-f33b2bf870e9 — grist

Fonte do frame: `f896f91781476b4f77e114b3cded95e233bfc860`, `help/en/docs/team-sharing.md`, data `2025-04-03`.

**Regra congelada:** A team may have at most 10 billing managers.

**Antes — frases removidas (exatas):**

```text
!!! note You can have up to 10 billing managers in the version of Grist at getgrist.com .
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: A team may have at most 10 billing managers.
- `gpt-6-sol`: A team on getgrist.com can have at most 10 billing managers.

**Observação positiva congelada:** With 10 billing managers already assigned, the web interface prevents assigning an eleventh.

**Observação negativa congelada:** The web interface allows an eleventh billing manager to be assigned.

**Revisão: Revisão V1 e escopo.** A regra congelada omite a qualificação in the version of Grist at getgrist.com, preservada por Sol. Um limite da edição hospedada não estabelece o mesmo limite para toda instalação/equipe. A fonte é somente removida. Limite de 10 é observável, mas A precisa fixar a edição e a versão.

### rc-c044ebec7fe1 — zulip

Fonte do frame: `94c98c574908e1bd5cc335a90bdb12915239f428`, `help/include/subscribe-user-to-channel.md`, data `2025-07-21`.

**Regra congelada:** The user subscription typeahead must exclude users already subscribed to the target channel.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
To subscribe users in bulk, you can copy members from an existing channel or user group .
```

```text
The typeahead will only include users who aren't already subscribed to the channel.
```

```text
Configure Send notification message to newly subscribed users as desired.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: The user subscription typeahead must exclude users already subscribed to the target channel.
- `gpt-6-sol`: The channel subscription typeahead includes only users who are not already subscribed to that channel.

**Observação positiva congelada:** The typeahead suggests matching users who are not subscribed and omits matching users already subscribed to the channel.

**Observação negativa congelada:** The typeahead suggests a user who is already subscribed to the channel.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-c30a4162188a — zulip

Fonte do frame: `0c301102ca4ec594b4005b55e3772ba8191be8b5`, `starlight_help/src/content/docs/edit-a-message.mdx`, data `2026-03-22`.

**Regra congelada:** A message the user has permission to edit must display the pencil edit icon.

**Antes — frases removidas (exatas):**

```text
If you do not see the pencil ( ) icon, you do not have permission to edit this message.
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: A message the user has permission to edit must display the pencil edit icon.
- `gpt-6-luna`: Users without permission to edit a message do not see the pencil icon for that message.

**Observação positiva congelada:** The pencil edit icon is visible for a message the user may edit.

**Observação negativa congelada:** The pencil edit icon is missing for a message the user may edit.

**Revisão: Revisão V1 e direção lógica.** A fonte removida diz ausência do ícone implica falta de permissão. Por contraposição, permissão implica presença do ícone: a regra congelada de Astra é logicamente sustentada pelo texto anterior. Luna afirma falta de permissão implica ausência do ícone, que é a inversa e não decorre dessa frase. Não tratar os dois votos como equivalentes. A regra continua apoiada apenas no texto removido.

### rc-277279fd03a4 — zulip

Fonte do frame: `8c409caa3ace4629ee5532ec52fecc32eec54ca2`, `help/set-default-channels-for-new-users.md`, data `2025-01-22`.

**Regra congelada:** Only public or web-public channels can be selected as default channels for new users.

**Antes — frases removidas (exatas):**

```text
When new users join a Zulip organization, they are subscribed to a default set of channels.
```

```text
Organization administrators can add or remove channels from that default set.
```

**Depois — frases adicionadas (exatas):**

```text
You can configure a default set of channels that users will be subscribed to when they join your organization.
```

```text
Default channels must be public or web-public .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Only public or web-public channels can be selected as default channels for new users.
- `gpt-6-sol`: Only public or web-public channels can be added to an organization's default channels.

**Observação positiva congelada:** A private channel cannot be selected as a default channel.

**Observação negativa congelada:** A private channel can be selected and saved as a default channel.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-c5ed01f3769c — zulip

Fonte do frame: `65c44b863e1ad89c44081757584a42200e85f256`, `starlight_help/src/content/docs/message-a-channel-by-email.mdx`, data `2026-01-06`.

**Regra congelada:** The button to generate a channel email address must be hidden when the user lacks permission to send messages to that channel.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
You will see the button to generate an email address only if you have permission to send messages to this channel.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: The button to generate a channel email address must be hidden when the user lacks permission to send messages to that channel.
- `gpt-6-sol`: The button to generate a channel email address is visible only to users who have permission to send messages to that channel.

**Observação positiva congelada:** A user without permission to send messages to the channel sees no button to generate an email address.

**Observação negativa congelada:** A user without permission to send messages to the channel sees the button to generate an email address.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-362ff82e3812 — zulip

Fonte do frame: `a11cc9a46e3f2eb077f4d271065944fc4a29786c`, `help/configure-automated-notices.md`, data `2025-05-14`.

**Regra congelada:** Users can configure whether automated notices are automatically marked as read.

**Antes — frases removidas (exatas):**

```text
These notices will be marked as unread only for users who had participated in the topic.
```

**Depois — frases adicionadas (exatas):**

```text
Users can configure whether these notices are automatically marked as read.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Users can configure whether automated notices are automatically marked as read.
- `gpt-6-sol`: A user's setting controls whether automated notices are automatically marked as read.

**Observação positiva congelada:** A web setting lets the user enable or disable automatically marking automated notices as read.

**Observação negativa congelada:** The web interface provides no way to change whether automated notices are automatically marked as read.

**Revisão: Revisão da observação-alvo.** A fonte e a regra congelada expressam configurabilidade de marcar notices como lidos. O pass/fail congelado verifica somente existência de um controle de configuração. Um controle que não altera nada satisfaria essa observação, sem demonstrar que o usuário consegue configurar o comportamento. Antes do oracle, distinguir disponibilidade do controle da alteração funcional do estado dos notices.

### rc-393307131fc8 — zulip

Fonte do frame: `7f68ccfa3d4023cd3b9b990392102aba8703b03e`, `help/pin-a-channel.md`, data `2025-08-04`.

**Regra congelada:** Enabling “Pin channel to top of left sidebar” in a channel’s Personal settings places that channel at the top of the left sidebar.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
Select a channel.  {!select-channel-view-personal.md!}  1.
```

```text
Under Personal settings , toggle Pin channel to top of left sidebar .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Enabling “Pin channel to top of left sidebar” in a channel’s Personal settings places that channel at the top of the left sidebar.
- `gpt-6-sol`: When a user turns on Pin channel to top of left sidebar for a channel, that channel appears at the top of the left sidebar.

**Observação positiva congelada:** After enabling the toggle, the selected channel appears at the top of the left sidebar.

**Observação negativa congelada:** After enabling the toggle, the selected channel remains below unpinned channels in the left sidebar.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-103dc930a420 — zulip

Fonte do frame: `1e49b01d8014eecefe58e66ce52a75fd63de5e1f`, `help/configure-default-new-user-settings.md`, data `2025-08-28`.

**Regra congelada:** When a user accepts an invitation, their initial settings must match the defaults configured at acceptance time.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
Users will have the initial settings that are configured at the time when they accept the invitation, so there's no need to update or revoke invitations when you change default settings.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: When a user accepts an invitation, their initial settings must match the defaults configured at acceptance time.
- `gpt-6-sol`: A user who accepts an invitation receives the default settings configured at the time of acceptance.

**Observação positiva congelada:** After defaults change while an invitation is pending, the invited user accepts and sees the updated defaults in their settings.

**Observação negativa congelada:** After defaults change while an invitation is pending, the invited user accepts and sees the earlier defaults in their settings.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-1590080019fb — grist

Fonte do frame: `4436beebb038b32128f9a924b24f9f63635ec755`, `help/en/docs/access-rules.md`, data `2026-01-28`.

**Regra congelada:** Structure (S) permissions must not be available in table-level access rules.

**Antes — frases removidas (exatas):**

```text
Structure ( S ) permissions are not available at the table level.
```

**Depois — frases adicionadas (exatas):**

(Nenhuma frase adicionada neste recorte.)

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Structure (S) permissions must not be available in table-level access rules.
- `gpt-6-sol`: Structure (S) permissions are unavailable at the table level.

**Observação positiva congelada:** The table-level access rule editor offers no selectable Structure (S) permission.

**Observação negativa congelada:** The table-level access rule editor allows selecting Structure (S) permission.

**Revisão: Revisão V1.** A indisponibilidade de Structure (S) no nível da tabela é explícita e observável, mas somente no texto removido. A presença no futuro A atual não está demonstrada pelo delta.

### rc-08dffa18a270 — zulip

Fonte do frame: `a31cd65175c5a219d83df9758829cb6f86cf24fa`, `starlight_help/src/content/docs/animated-gifs.mdx`, data `2026-03-25`.

**Regra congelada:** Setting GIF picker to Disabled in Compose settings removes the GIF picker from the compose box.

**Antes — frases removidas (exatas):**

```text
Under Compose settings , select a rating for GIF integration .
```

**Depois — frases adicionadas (exatas):**

```text
Under Compose settings , select a rating for GIF picker .
```

```text
Disable the GIF picker    Disabling the GIF picker removes it from the compose box.
```

```text
Under Compose settings , set GIF picker to Disabled .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Setting GIF picker to Disabled in Compose settings removes the GIF picker from the compose box.
- `gpt-6-sol`: When a user sets GIF picker to Disabled in Compose settings, the GIF picker disappears from the compose box.

**Observação positiva congelada:** The compose box does not show the GIF picker after it is disabled.

**Observação negativa congelada:** The compose box still shows the GIF picker after it is disabled.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-b7086f489030 — zulip

Fonte do frame: `854c7d4ea850422fdd6a4740ead856a28fded261`, `help/restrict-message-editing-and-deletion.md`, data `2025-07-17`.

**Regra congelada:** A channel's Moderation permissions must allow users to configure who can delete their own messages in that channel.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
Configure who can delete messages in a specific channel  {start_tabs}  {tab|desktop-web}  {relative|channel|all}  1.
```

```text
Select a channel.  {!select-channel-view-general-advanced.md!}  1.
```

```text
Under Moderation permissions , configure Who can delete any message in this channel and Who can delete their own messages in this channel .  {!save-changes.md!}  {end_tabs}
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: A channel's Moderation permissions must allow users to configure who can delete their own messages in that channel.
- `gpt-6-luna`: A channel's moderation settings determine who can delete any message in that channel and who can delete their own messages there.

**Observação positiva congelada:** The channel's Moderation permissions show an editable setting labeled "Who can delete their own messages in this channel".

**Observação negativa congelada:** The channel's Moderation permissions provide no setting for who can delete their own messages in that channel.

**Revisão: Revisão da unidade-alvo e observação.** A fonte adicionada tem dois settings distintos: who can delete any message e who can delete their own messages. A regra congelada escolhe apenas own; Luna inclui os dois. O pass/fail congelado observa apenas existência de setting editável com esse rótulo, sem salvar configuração nem demonstrar seus efeitos. O texto inclui save-changes; presença do controle não basta para provar a capacidade de configurar.

### rc-aac66a0af69a — grist

Fonte do frame: `4c173049c5eee0664b5e3fa754550e0d1c71fa2a`, `help/en/docs/document-tutorials.md`, data `2025-06-03`.

**Regra congelada:** Clicking Restart at the bottom of the tutorial popup refreshes the page and discards unsaved changes.

**Antes — frases removidas (exatas):**

```text
⚠️ Important: Always replace the original before restarting the tutorial.
```

```text
If you click Restart Tutorial first, any unsaved changes will be lost.
```

**Depois — frases adicionadas (exatas):**

```text
⚠️ Important: Clicking 'Restart' at the bottom of the tutorial popup will refresh the page, causing any unsaved changes to be lost.
```

```text
Be sure to save changes to the main document *prior* to clicking this.  *! review-option1 *
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Clicking Restart at the bottom of the tutorial popup refreshes the page and discards unsaved changes.
- `gpt-6-sol`: Clicking Restart at the bottom of the tutorial popup refreshes the page.

**Observação positiva congelada:** After clicking Restart with an unsaved edit, the page reloads and the edit is absent.

**Observação negativa congelada:** After clicking Restart with an unsaved edit, the edit remains.

**Revisão: Revisão da unidade-alvo.** A regra congelada contém refresh da página E perda de mudanças não salvas, ambos explícitos na fonte adicionada. Sol conserva apenas refresh. A perda é a consequência que o pass/fail congelado verifica; um refresh que preserva edits distingue concretamente os votos. Confirmar a obrigação manipulada e o span correspondente, sem escolher outra por resultados.

### rc-4200f1dac6a9 — zulip

Fonte do frame: `3ca12e7224e7158d866f3d24f52ce877749fb742`, `starlight_help/src/content/docs/add-a-custom-linkifier.mdx`, data `2026-03-03`.

**Regra congelada:** When a user pastes a URL matching a reverse-enabled linkifier into the compose box, it automatically becomes linked text corresponding to that linkifier.

**Antes — frases removidas (exatas):**

```text
If the pattern appears in a topic, Zulip adds an Open ( ) button to the right of the topic in the message recipient bar that links to the appropriate URL.
```

**Depois — frases adicionadas (exatas):**

```text
You can configure linkifiers to work in reverse as well: when you paste a URL that matches the linkifier into the compose box, Zulip will automatically convert it to linked text (e.g., https://github.com/zulip/zulip/issues/2468 becomes #2468 ).
```

```text
If a linkifier pattern (e.g., #2468 ) appears in the name of a topic, Zulip adds an Open ( ) button to the right of the topic in the message recipient bar that links to the appropriate URL.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: When a user pastes a URL matching a reverse-enabled linkifier into the compose box, it automatically becomes linked text corresponding to that linkifier.
- `gpt-6-sol`: When a user pastes a URL matching a configured reverse linkifier into the web compose box, Zulip automatically converts it to linked text.

**Observação positiva congelada:** The pasted URL appears as the corresponding linked text, such as #2468, linking to the original URL.

**Observação negativa congelada:** The matching pasted URL remains a raw URL instead of becoming the corresponding linked text.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-adf56e244737 — zulip

Fonte do frame: `11b90c66bf115d2dd4ccf7de89ab4030ee5cd5ae`, `starlight_help/src/content/docs/search-for-messages.mdx`, data `2026-04-14`.

**Regra congelada:** Searching for channels:archived returns only messages the user received in archived channels.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
channels:archived : Search the messages you received in archived channels .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Searching for channels:archived returns only messages the user received in archived channels.
- `gpt-6-sol`: Searching for channels:archived shows messages the user received in archived channels.

**Observação positiva congelada:** With received messages in both active and archived channels, the search results show only those in archived channels.

**Observação negativa congelada:** The search results include a message from an active channel.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-f0b216964e6f — grist

Fonte do frame: `05e768aedf8188dcac618085686c55ce82b444e3`, `help/en/docs/widget-table.md`, data `2025-10-01`.

**Regra congelada:** Conditional formatting added under 'Row Style' must apply across the entire matching table row.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
Customize row height : In the widget options panel, you can set a max row height which sets a maximum number of lines for multi-line text.
```

```text
Additionally, you can choose to 'Expand all rows to this height' and set a consistent row height throughout your table.  ! max-row-height * {: .screenshot-half }  Add conditional styles : In the widget options panel, you can add conditional formatting for rows.
```

```text
When added under 'Row Style', the conditional styling will apply across the entire row.  ! conditional-styling-rows * {: .screenshot-half }
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: Conditional formatting added under 'Row Style' must apply across the entire matching table row.
- `gpt-6-sol`: Conditional formatting added under Row Style applies across the entire row.

**Observação positiva congelada:** Every cell in a row matching the condition displays the configured row styling.

**Observação negativa congelada:** Only some cells in a row matching the condition display the configured row styling.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

### rc-fd348eb33246 — zulip

Fonte do frame: `befe49c293c7cc490d4dfb94b387411591d1f114`, `help/channel-permissions.md`, data `2025-02-12`.

**Regra congelada:** Conversations in a private channel are visible to users who have been granted access to that channel.

**Antes — frases removidas (exatas):**

```text
zulip-icon-lock"> ) are for conversations that should be accessible only to users who are specifically subscribed to the channel.
```

**Depois — frases adicionadas (exatas):**

```text
zulip-icon-lock"> ) are for conversations that should be visible to users who are specifically granted access.
```

**Votos favoráveis — regras exatas:**

- `gpt-6-luna`: A private channel is visible only to users who have been specifically granted access.
- `gpt-6-sol`: Conversations in a private channel are visible to users who have been granted access to that channel.

**Observação positiva congelada:** A user granted access can see the channel's conversations.

**Observação negativa congelada:** A user granted access cannot see the channel's conversations.

**Revisão: Revisão da direção/escopo do outro voto.** A fonte adicionada e a regra congelada afirmam visibilidade das conversas para quem recebe acesso. Luna afirma visibilidade SOMENTE para quem recebe acesso, condição de exclusividade que não está expressa no trecho adicionado. A palavra only está no texto removido, vinculada a subscribed, outro critério. Não equiparar a regra de concessão positiva à proibição para todos os demais.

### rc-6be0f3992b4b — grist

Fonte do frame: `a3b9c0e79d7bc418ffb5785921428a052e6461c2`, `help/en/docs/document-settings.md`, data `2025-07-02`.

**Regra congelada:** On every plan, a document's combined attachment and data storage must not exceed 1GB.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
!!! note "Internal Attachment Limits" Attachments plus data in a single document are limited to 1GB on all plans.
```

```text
You can check your document's usage under Raw Data .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: On every plan, a document's combined attachment and data storage must not exceed 1GB.
- `gpt-6-sol`: A document cannot exceed 1GB of combined attachments and data, regardless of plan.

**Observação positiva congelada:** The web interface rejects an attachment upload that would bring the document's combined attachment and data storage above 1GB.

**Observação negativa congelada:** The web interface accepts an attachment upload that brings the document's combined attachment and data storage above 1GB.

**Revisão: Revisão V1 e escopo/mecanismo do oracle.** O trecho adicionado está sob Internal Attachment Limits. A regra congelada generaliza attachments+data por documento em todos os planos, sem registrar o escopo de armazenamento interno. O pass/fail exige rejeição do upload; o texto estabelece limite, mas não esse mecanismo específico. Há remoção explícita da mesma regra no mesmo arquivo em 2025-07-09, sete dias após sua adição: ela não deve ser tratada automaticamente como documentação atual. Verificar fonte completa/versão, escopo interno vs externo e observação do limite antes do A/oracle.

**Mudança relacionada:** `rc-d6bd85b5701d`, commit `10fe0a23d9f3ebc3dc8753221ed3e361fe8924c4`, data `2025-07-09`, arquivo `help/en/docs/document-settings.md`.

Frases removidas exatas:

```text
!!! note "Internal Attachment Limits" Attachments plus data in a single document are limited to 1GB on all plans.
```

Frases adicionadas exatas:

```text
!!! note "Attachment Limits" Attachment limits for all plans can be found here .
```

### rc-cb144c65d898 — zulip

Fonte do frame: `887e6e02830e7188859faffeb9b83107da442792`, `help/configure-who-can-invite-to-channels.md`, data `2025-03-07`.

**Regra congelada:** The channel settings screen must place the "Who can subscribe anyone to this channel" setting under "Advanced configurations".

**Antes — frases removidas (exatas):**

```text
Under Channel permissions , configure Who can subscribe anyone to this channel .
```

**Depois — frases adicionadas (exatas):**

```text
Under Advanced configurations , configure Who can subscribe anyone to this channel .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: The channel settings screen must place the "Who can subscribe anyone to this channel" setting under "Advanced configurations".
- `gpt-6-sol`: The “Who can subscribe anyone to this channel” setting appears under Advanced configurations.

**Observação positiva congelada:** The setting appears under "Advanced configurations".

**Observação negativa congelada:** The setting appears under "Channel permissions" instead of "Advanced configurations".

**Revisão: Revisão V1 e V2.** A mudança troca a localização do setting de Channel permissions para Advanced configurations. A regra e pass/fail congelados verificam apenas localização do controle, sem comportamento condicional ou consequência da política: isso precisa da mesma revisão V2 aplicada a rótulos/layout na rodada anterior. O próprio frame registra outra mudança em 2025-07-10, de Advanced configurations para Subscription permissions, após a adição de 2025-03-07; Advanced configurations não pode ser assumido como localização atual sem fonte completa.

**Mudança relacionada:** `rc-56a8f7377226`, commit `df98dd11ea0eb82f87804ed1bd452b5aa2aa8851`, data `2025-07-10`, arquivo `help/configure-who-can-invite-to-channels.md`.

Frases removidas exatas:

```text
Under Advanced configurations , configure Who can subscribe anyone to
```

Frases adicionadas exatas:

```text
Under Subscription permissions , configure Who can subscribe anyone to
```

### rc-b0a9c3fd790a — grist

Fonte do frame: `86df777926e2a2c7bc0932faa51700bae28921b3`, `help/en/docs/accessibility.md`, data `2026-05-18`.

**Regra congelada:** A screen reader must announce Markdown content beginning with '# ' as a heading rather than reading the hash symbol aloud.

**Antes — frases removidas (exatas):**

(Nenhuma frase removida neste recorte.)

**Depois — frases adicionadas (exatas):**

```text
Markdown content is vocalized by interpreting semantics instead of vocalizing the symbols.
```

```text
For example, # Content title is vocalized as "heading Content title" instead of letting the screen reader vocalize the # .
```

**Votos favoráveis — regras exatas:**

- `gpt-6-astra`: A screen reader must announce Markdown content beginning with '# ' as a heading rather than reading the hash symbol aloud.
- `gpt-6-sol`: In the web interface, a screen reader announces Markdown headings by their heading semantics rather than reading the Markdown # symbol.

**Observação positiva congelada:** The screen reader announces '# Content title' as 'heading Content title'.

**Observação negativa congelada:** The screen reader reads the hash symbol aloud instead of announcing a heading.

**Revisão: Sem divergência concreta detectada no recorte.** O trecho adicionado expressa a regra congelada e seu resultado observável. As diferenças entre votos não demonstram outra obrigação no material lido. Isso não certifica presença na documentação atual, futura fixture/oracle, licença ou admissão final.

## Pendências antes da seleção/E2Es

Os flags exigem revisão humana do mapping, da versão de A, do escopo e/ou do oracle. Não se recomenda aqui manter, excluir, trocar a regra ou priorizar qualquer candidato. Se uma regra mudar, registrar a decisão e a relação entre a regra original congelada e a nova antes de interpretar medidas posteriores. Qualificação de fixture, oracle independente, licença, deduplicação e seleção única continuam gates separados.
