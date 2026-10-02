# Triagem por consenso de LLMs

Modelos primários: gpt-6-astra, gpt-6-sol. Desempate: gpt-6-luna.

Os três modelos passaram nos seis controles: 18 decisões de qualificação. Isso é triagem assistida por LLMs; não é revisão humana nem evidência confirmatória de H1/H2.

Foram avaliados 258 candidatos: 69 admitidos, 189 excluídos e 0 sem resolução.

Kappa dos modelos primários: 0,844964, em 258 pares com dois votos válidos. Votos ausentes/inválidos: 0.

| Projeto | Admitidos |
|---|---:|
| immich | 4 |
| mattermost | 15 |
| mealie | 3 |
| nextcloud | 10 |
| openproject | 17 |
| paperless | 5 |
| wekan | 15 |

Rotas recalculadas: {"agreement": 239, "tiebreaker": 16, "pilot_case_mechanical": 3}.

Exclusões mecânicas de pilotos já utilizados: 3; são separadas das exclusões decididas pelo painel.

Há 67 candidatos admitidos com textos de regra-alvo distintos entre os votos favoráveis. Isso não demonstra conflito semântico; o relatório preserva os textos sem escolher uma resolução.

O pré-registro exige pelo menos 30 requisitos de pelo menos oito projetos, com **no máximo seis requisitos por projeto**. Se houver mais de seis admitidos em um projeto, a seleção posterior sorteia seis com seed 2026100203. O teto não limita a triagem inteira nem significa seis projetos. Este relatório não executa essa seleção. Aplicar o teto aos admitidos atuais permite no máximo 36 requisitos, mas há apenas sete projetos; portanto, o requisito de pelo menos oito projetos ainda não foi cumprido.

Permanece prevista auditoria humana aleatória de 20% das decisões antes de qualquer afirmação confirmatória. Não foram atribuídos rótulos de smells.

Divergências entre resultado armazenado e recálculo: 0 linhas e 0 campos do resumo.

## Textos de regra-alvo para comparação

Diferenças textuais podem ser apenas paráfrases. Esta lista não classifica todos esses pares como divergências semânticas.

### rc-882709afd891 (mattermost)

- gpt-6-astra: When a user mentions someone who is not a member of the channel, the web interface prompts them to add that person to the channel.
- gpt-6-sol: When a user mentions someone who is not a channel member, the web interface prompts to add that person to the channel.

### rc-302720d6856b (openproject)

- gpt-6-astra: Switching a work package from manual to automatic scheduling displays a warning banner stating that its dates are not determined by child work packages.
- gpt-6-sol: When a user switches a work package from manual to automatic scheduling, a warning banner says its dates are not determined by child work packages.

### rc-1986ea85580a (openproject)

- gpt-6-astra: By default, newly created work packages display numerical IDs from a single instance-wide sequence, regardless of project.
- gpt-6-sol: By default, a newly created work package receives a unique ID from an instance-wide numerical sequence.

### rc-9c57cc2cca50 (wekan)

- gpt-6-astra: When the user selects the 1 Board option for multiline text, the whole text is kept as one board title.
- gpt-6-sol: When a user enters multiline text to create one board, the board keeps the entire text as one title.

### rc-ca08cec6ec87 (openproject)

- gpt-6-astra: Each meeting agenda section must display the sum of the specified durations of its contained items.
- gpt-6-sol: A meeting section displays the sum of the durations specified for its agenda items.

### rc-84013890a131 (paperless)

- gpt-6-sol: Documents whose processed text is empty or contains only whitespace are skipped.
- gpt-6-luna: Documents with processed text that is empty or contains only whitespace are skipped.

### rc-e436521e462d (openproject)

- gpt-6-astra: The project’s attachment visibility setting determines whether the attachments option appears in the Files tab of its work package detailed views.
- gpt-6-sol: When the Attachments option is deactivated in a project's Files settings, it is not shown under the Files tab in that project's work package detail view.

### rc-458cc4cba31a (wekan)

- gpt-6-astra: Duplicating a board with either duplication option excludes the source board's existing board and card activity events from the duplicate's activity history.
- gpt-6-sol: Duplicating a board, with or without cards, creates a board whose activity history excludes the source board’s existing board and card events.

### rc-d3faa64f9193 (nextcloud)

- gpt-6-astra: The web interface must allow a user to start a discussion thread with a title and description.
- gpt-6-sol: The web interface lets a user add a title and description when starting a discussion thread.

### rc-c38fa60b1164 (nextcloud)

- gpt-6-astra: Confirming Delegate access makes the shared mail account appear in the selected delegate's account list marked as delegated.
- gpt-6-sol: After an account owner grants another user access to a mail account, that account appears in the delegate's account list marked as delegated.

### rc-0284c8781546 (mattermost)

- gpt-6-astra: Playbook task text containing Markdown is displayed with Markdown formatting.
- gpt-6-sol: Text in a playbook task is rendered as Markdown when Markdown formatting is present.

### rc-0ec1ac8f66bd (immich)

- gpt-6-astra: The web upload interface accepts MP2T video files with the .m2t extension.
- gpt-6-sol: The web interface accepts .m2t video files as a supported MP2T format.

### rc-59d96b056593 (wekan)

- gpt-6-astra: Toggling “Show week of year (ISO 8601)” in the board Date popup immediately updates the week-number display without requiring Save.
- gpt-6-sol: In the board Date popup, toggling Show week of year (ISO 8601) immediately updates the user's week-number display preference.

### rc-0dde4b87ef72 (nextcloud)

- gpt-6-astra: When a chat poll is anonymous, participants cannot see who voted for each option.
- gpt-6-sol: In an anonymous chat poll, participants cannot see which person voted for each option.

### rc-57edf89f8e91 (wekan)

- gpt-6-astra: Standard Duplicate links display as duplicates or is-duplicated-by according to their direction.
- gpt-6-sol: A standard Duplicate link appears as duplicates or is-duplicated-by according to its direction.

### rc-de652e658b99 (wekan)

- gpt-6-astra: After a logged-in reader stars a public board they do not belong to and reloads, that board appears in their Starred overview.
- gpt-6-sol: A logged-in reader can star a public board they do not belong to.

### rc-1114153d4704 (openproject)

- gpt-6-astra: Changing the work package table configuration automatically updates the results displayed in the table.
- gpt-6-sol: When a user changes the work package table configuration, the table automatically updates to display the matching results.

### rc-babbaaab4a5e (mattermost)

- gpt-6-astra: Attachments restricted by attribute-based permissions must appear in messages with the placeholder "Files not available" and subtitle "Access to files is restricted based on attributes".
- gpt-6-sol: When a message contains an attachment the user cannot access because of attribute-based permissions, the web interface shows the placeholder “Files not available” with the subtitle “Access to files is restricted based on attributes.”

### rc-fbc75725d8ad (mattermost)

- gpt-6-astra: Guests using a magic login link can log in through the web interface without entering a password.
- gpt-6-sol: A guest invited with a magic link can log in through that link without entering a password.

### rc-4efba0098a79 (openproject)

- gpt-6-astra: The project's More (three dots) dropdown menu must include an "Add a subproject" option.
- gpt-6-sol: The project settings More menu includes an Add a subproject option.

### rc-4fa8e7483b1a (mattermost)

- gpt-6-astra: The timezone preference defaults to Automatic.
- gpt-6-sol: The web interface defaults the timezone preference to Automatic, which uses the computer's timezone.

### rc-27e586be0e1e (openproject)

- gpt-6-sol: When a work package description contains page breaks, the exported document splits its contents into separate pages at those breaks.
- gpt-6-luna: When a work package description contains page breaks, the exported contents are split across separate pages at those breaks.

### rc-2c13970217ea (openproject)

- gpt-6-astra: An archived project must not appear as a selectable option in the project selector.
- gpt-6-sol: An archived project does not appear in the project selector.

### rc-554bcd113361 (mattermost)

- gpt-6-astra: Channel messages are automatically translated into the user's preferred language.
- gpt-6-sol: Channel messages are automatically displayed in the user's preferred language.

### rc-ebff8e70d1d7 (wekan)

- gpt-6-astra: Duplicating a board does not copy the source board's existing board or card activity events into the duplicate.
- gpt-6-sol: Duplicating a board does not copy the source board’s existing activity events into the new board’s activity history.

### rc-899c4d2472ad (wekan)

- gpt-6-astra: Reordering a field in either display-order list changes its position on the corresponding card surface without changing its position on the other surface.
- gpt-6-sol: On a board, the minicard and card display fields in the top-to-bottom order of their respective lists.

### rc-17b31565c57c (openproject)

- gpt-6-astra: When inviting a new member, the web interface must allow selecting an existing user role, group, or placeholder user's permissions as the basis for the new user's permissions.
- gpt-6-sol: When inviting a new member, the web interface lets the inviter choose whether the new user's permissions are based on an existing user role, a group, or a placeholder user's permissions.

### rc-afa7beacea83 (immich)

- gpt-6-astra: The folder feature toggle under Account Settings > Features is labeled "Folders".
- gpt-6-luna: Enabling Folders under Account Settings > Features makes the folder view available in the web interface.

### rc-ab0227c1eb5b (nextcloud)

- gpt-6-astra: When Sort favorites up is enabled in Mail appearance settings, favorite messages appear in a separate section above the rest of the message list.
- gpt-6-sol: When Sort favorites up is enabled, favorite messages appear in a separate section above the rest of the message list.

### rc-4041140f2b5d (wekan)

- gpt-6-astra: When dragging an archived multi-selection, the destinations highlighted in green must be exactly Remaining and all existing Workspaces.
- gpt-6-sol: Dropping an archived selection of boards onto a Workspace restores every selected board and assigns it to that Workspace.

### rc-024102998dd2 (wekan)

- gpt-6-sol: In a PDF viewed from the web interface, an attachment with a displayed preview does not appear in the attachment bullet list.
- gpt-6-luna: The attachment list includes only files without a displayed preview, while successfully previewed images appear once with their filename in the caption and unreadable previews or non-image attachments remain listed with filename and size.

### rc-3fbc295441e2 (mattermost)

- gpt-6-astra: When inviting a guest, the user must select at least one channel before the invitation can be submitted.
- gpt-6-sol: A guest invitation requires at least one selected channel.

### rc-d595b3b1510f (nextcloud)

- gpt-6-astra: The conversation settings Meeting section must offer a CSV upload option for bulk inviting email participants.
- gpt-6-sol: The Meeting section of a conversation’s settings lets a user upload a CSV file to invite multiple email participants.

### rc-290b3ea47ca2 (wekan)

- gpt-6-astra: Jira import must preserve status names as literal text, including names such as constructor or proto.
- gpt-6-sol: When importing a Jira file, the web interface treats status names such as constructor and proto as literal status names.

### rc-806442660eb5 (paperless)

- gpt-6-astra: A user may grant superuser status to another user only if the acting user is a superuser.
- gpt-6-sol: In the web interface, only a superuser can grant superuser status to another user.

### rc-276016ee58a0 (openproject)

- gpt-6-astra: Users can set work package start and finish dates by typing into the corresponding date fields.
- gpt-6-luna: Users can enter dates in the start and finish date fields by typing them.

### rc-6fb3a96cddc0 (openproject)

- gpt-6-astra: When project wikis are disabled globally, the Project wiki settings page remains visible and displays a notice that wikis must first be enabled globally in administration settings.
- gpt-6-sol: When project wikis are disabled globally, the Project wiki settings page remains visible and tells users that wikis must first be enabled in administration settings.

### rc-6337ce108c4d (openproject)

- gpt-6-sol: Only administrators can see the options to set a project as a template or remove it from templates.
- gpt-6-luna: The project settings display an icon for setting the project as a template.

### rc-086a9d210266 (paperless)

- gpt-6-astra: Adding a custom field to a document without specifying a value must preserve any existing value of that field on the document.
- gpt-6-sol: Adding a custom field to a document without specifying a value leaves any existing value of that field unchanged.

### rc-b6b9f39b947a (mattermost)

- gpt-6-sol: A persistent notification for an urgent message containing an @mention stops repeating when its recipient acknowledges, reacts to, or replies to the message.
- gpt-6-luna: An urgent message with an @mention repeats notifications to its recipient until they acknowledge, react, or reply.

### rc-60c42d4dd323 (mealie)

- gpt-6-astra: With Food enabled, shopping-list entries for 1 cup of cheese and 2 cups of cheese must combine into one entry showing 3 cups of cheese.
- gpt-6-sol: Shopping list items marked as Food with the same ingredient and unit are combined by adding their quantities.

### rc-15ed48fe86b0 (mattermost)

- gpt-6-sol: In a new Mattermost deployment, users can create threads by default.
- gpt-6-luna: All Mattermost users can create new threads unless the system admin has disabled threaded discussions.

### rc-c86728bbc029 (immich)

- gpt-6-astra: When creating an external library, the web interface must allow assigning it to exactly one user.
- gpt-6-sol: An external library can belong to only one user, selected when the library is created.

### rc-e594b40135ff (nextcloud)

- gpt-6-astra: Creating a Calendar event with a Talk conversation as its location creates a conversation visible in the conversation list if none exists yet.
- gpt-6-sol: When a Calendar event is created with a Talk conversation as its location, the event details show a link to that conversation.

### rc-9d801a70d5d2 (nextcloud)

- gpt-6-astra: Deleting a folder under normal conditions moves it to the trash bin instead of permanently deleting it.
- gpt-6-sol: When a user deletes a file or folder in the web interface, it normally moves to the trash bin and can be restored.

### rc-476f8413ae2e (mattermost)

- gpt-6-astra: The Quarantine for Review action is available only for messages in public or private channels, not in direct or group messages.
- gpt-6-sol: The Quarantine for Review action is available for messages in public and private channels, but unavailable in direct and group messages.

### rc-969f81480445 (openproject)

- gpt-6-astra: A linked work package is displayed as a full-width card only when linked using a slash command on an empty line.
- gpt-6-sol: A work package linked with a slash command on an empty line is displayed as a full-width card.

### rc-16b088247c39 (nextcloud)

- gpt-6-astra: Users can configure a default reminder for all events in a calendar through that calendar's settings.
- gpt-6-sol: When a user sets a default reminder in a calendar’s settings, events in that calendar have that reminder by default.

### rc-54a0e2c483c4 (mattermost)

- gpt-6-astra: When leaving an already-muted public channel joined through a membership policy, the confirmation dialog shows Cancel and Leave channel instead of Mute instead.
- gpt-6-sol: When a user tries to leave an already muted public channel they joined through a membership policy, the confirmation offers Cancel and Leave channel instead of Mute.

### rc-b6f382226c41 (immich)

- gpt-6-astra: In Full path or folder search mode, a query matching part of an asset's original path must include that asset in the results.
- gpt-6-sol: In Full path or folder search mode, entering a term that matches part of an asset’s original path returns that asset.

### rc-106bac72c813 (mealie)

- gpt-6-astra: A user must have Organize group data permission to create a new food through the web interface.
- gpt-6-sol: A user without Organize group data permission cannot create a new food while parsing a recipe.

### rc-aa2c82f86e08 (mattermost)

- gpt-6-astra: When anonymous team and channel URLs are enabled, the web team creation flow assigns the team URL automatically without prompting the user to choose it.
- gpt-6-sol: When anonymous team and channel URLs are enabled, creating a team does not prompt the user to choose a team URL; the URL is assigned automatically.

### rc-f3df2f6e5885 (wekan)

- gpt-6-astra: Synchronizing an upstream title or description change updates the corresponding card text only if it still matches the last synchronized source value, preserving locally edited text otherwise.
- gpt-6-sol: When a card is synchronized, an upstream title or description change updates that field only if its local text still matches the last synchronized source value.

### rc-8b05adc7767e (wekan)

- gpt-6-astra: When either membership restriction is enabled, a non-admin inviter can add a user to a board only if that user shares an organization or team of an enabled kind with the inviter or an active board member.
- gpt-6-sol: When an organization-only or team-only restriction is enabled, a non-admin user can add someone to a board only if that person shares an enabled kind of membership with the inviter or an active board member.

### rc-03a505847a99 (mattermost)

- gpt-6-astra: A user with channel permission to create checklists can create a checklist in that channel without separate playbook access permissions.
- gpt-6-sol: A user with permission to create channel checklists can create one without playbook access.

### rc-02df56f00b58 (openproject)

- gpt-6-astra: When automatic theme mode is selected, OpenProject must match the operating system’s contrast setting.
- gpt-6-sol: When automatic theme matching is selected, OpenProject applies the operating system’s contrast setting.

### rc-88440629ecb6 (wekan)

- gpt-6-astra: Dropping multiple selected boards onto Home must display "Please select only one board" while leaving Home and the selection unchanged.
- gpt-6-sol: Dropping a selection of multiple boards on Home shows “Please select only one board” without changing Home or clearing the selection.

### rc-bd0b2995febc (mattermost)

- gpt-6-astra: Users can submit a status update without setting a reminder for the next status update.
- gpt-6-sol: On the first status update, a playbook’s default reminder timer is preselected when one is defined.

### rc-0c831f7cb825 (openproject)

- gpt-6-astra: The OpenProject date picker must display a yellow banner warning that manual scheduling will ignore existing relations.
- gpt-6-sol: When a user selects manual scheduling in the work package date picker, a yellow banner warns that existing relations will be ignored.

### rc-035e8af08cd7 (paperless)

- gpt-6-astra: A user without User management permissions can edit their own profile through My Profile.
- gpt-6-sol: A user can edit their own profile through My Profile without permission to manage other user accounts.

### rc-946f02ef19b6 (nextcloud)

- gpt-6-sol: Using breakout rooms in a web call divides the call into smaller groups.
- gpt-6-luna: Users with the necessary permissions on an instance where the feature is enabled can divide a call into smaller groups using breakout rooms.

### rc-49aaaf2e6630 (openproject)

- gpt-6-astra: When shared sprint fields are read-only due to permissions, the project-specific sprint goal remains independently editable.
- gpt-6-sol: A user whose permissions make shared sprint fields read-only can still edit the project-specific sprint goal.

### rc-4da4940bc16c (mattermost)

- gpt-6-astra: When the feature is enabled, channel admins creating a channel see a field labeled “Default category (optional)”.
- gpt-6-sol: When a channel admin sets a default category for a channel, a member who joins the channel sees it under that category in their sidebar.

### rc-90d29a54a512 (wekan)

- gpt-6-astra: Changing the section display order for an opened card must not change the minicard's section display order.
- gpt-6-sol: The minicard shows its selected fields in its selected order independently of the opened card’s display settings.

### rc-3d153b91ab4e (nextcloud)

- gpt-6-astra: A device password is accessible in the web interface only when it is created.
- gpt-6-sol: The device password is visible only while it is being created.

### rc-0f453b1f0a55 (mealie)

- gpt-6-astra: A recipe-pool rule using a Food Label includes only recipes with an ingredient bearing that label.
- gpt-6-sol: A recipe pool rule based on an ingredient’s Food Label includes recipes containing ingredients with that label.

### rc-9e198862b86e (paperless)

- gpt-6-astra: The {{doc_title}} placeholder cannot be used in title assignment.
- gpt-6-sol: The web interface must not allow {{doc_title}} in a document title assignment.


## Custódia e alcance

Foram 550 chamadas, incluindo 18 controles, 516 votos primários e 16 desempates, sem falhas, respostas inválidas ou retries. Os 3.569 arquivos do pacote privado foram verificados por SHA-256. Votos e recálculo públicos: `data/llm-screening-20261002/`. Capturas brutas do CLI permanecem privadas.

Os 69 admitidos são candidatos elegíveis segundo o painel. Isso não é confirmação de 69 smells nem consenso independente sobre cada regra-alvo. Ainda requer comparação substantiva dos mappings, licença e escopo do oráculo antes de geração de implementações. A sonda usa a regra e pergunta selecionadas pelo mecanismo congelado; recuperar uma regra sem referência não identifica a origem desse conhecimento.

## Leitura adicional do assistente, após a triagem

Esta leitura não altera votos ou admissões nem substitui revisão independente. Sete candidatos apresentam escolhas substantivamente diferentes de condição observável entre votos favoráveis:

| Candidato | Condições diferentes |
|---|---|
| rc-de652e658b99 | Persistência no overview após reload / possibilidade de favoritar |
| rc-afa7beacea83 | Texto do toggle Folders / disponibilidade da visão de pastas |
| rc-4041140f2b5d | Destinos destacados ao arrastar / restaurar e atribuir ao soltar |
| rc-6337ce108c4d | Restrição dos controles a administradores / existência do ícone |
| rc-e594b40135ff | Criar conversa Talk / exibir link no evento |
| rc-bd0b2995febc | Reminder opcional / preseleção do reminder padrão |
| rc-4da4940bc16c | Campo de categoria / posição do canal na sidebar de quem entra |

Esses sete mappings permanecem pendentes antes de admitir implementações no experimento. O kappa é das decisões admit/exclude, não da equivalência das regras-alvo.

A pergunta de rc-60c42d4dd323 menciona duas quantidades de queijo sem informá-las, embora a regra escolhida fixe 1 cup + 2 cups → 3 cups. Isso pode produzir um negativo mesmo quando o modelo conhece a agregação geral. rc-b6f382226c41 pergunta pelo resultado de Printing sem inventário; sua regra-alvo é geral, então uma resposta com o predicado de busca no path pode ser suficiente, sem nomear um asset. É uma sensibilidade de escopo, não uma pergunta demonstradamente inválida. Não foram encontrados exemplos claros em que a pergunta enuncie a resposta-alvo. A execução original não foi alterada ou repetida.
