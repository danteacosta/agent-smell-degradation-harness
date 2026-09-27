# Nextcloud Delete permanently: instrumento adiado

O candidato exige que, na tela **Deleted files**, clicar em **Delete
permanently** remova o item selecionado. Uma réplica de navegador verifica
ausência após recarga e preservação de outro item. O oráculo técnico passou
**8/8 controles**: duas implementações corretas, mutantes alvo e não alvo,
ocultação apenas visual, exclusão antecipada, handler ausente e erro de script.
Seu recibo privado é
`81f0786ed6cadd8aa5043ab41b3ba90f61c806746562ff722d151c46ebe331cc`.

O gate de mapeamento científico **não passou**. Na primeira revisão, os três
julgadores rejeitaram a formulação que tratava remoção e persistência após
recarga como obrigações distintas. Uma segunda formulação tratou a remoção
como obrigação única e a recarga como técnica de observação; recebeu dois
ACCEPT e um REJECT. A objeção remanescente foi que o trecho da fonte diz
"permanently deleted", mas não explicita a ausência na lista visível como
endpoint. O recibo privado da segunda revisão é
`15d7e11357c2a8cfe07dd77fd4015e887034f7d1992ca379f9fe3e323f743251`.

**Nenhuma geração foi feita para este candidato.** O instrumento fica
disponível para eventual revisão de fonte ou endpoint, mas não é uma obrigação
executada nem evidência para H1/H2. A qualificação do software, por si só,
não resolve o desacordo de validade de construto.

A [consulta posterior à documentação oficial](2026-09-27-nextcloud-permanent-delete-source.md)
confirmou o vínculo entre o comando **Delete permanently** e a exclusão do
item da lixeira, mas não enuncia o estado exato da lista após recarga. O voto
discordante original permanece válido como registro e nenhuma geração foi
admitida por essa consulta isolada.

Uma revisão nova do endpoint removeu a inspeção de `deleteBehavior`, estado
privado do scaffold. O navegador agora exige que o botão selecionado esteja
visível e habilitado antes do clique, e observa a lista após recarga. A/B/C
estão em
[arms-20260927.json](../../data/e2e-nextcloud-permanent-delete/arms-20260927.json).
O oráculo v2 passou **8/8 controles** no Chromium fixado, recibo
`13559624b49659b68044bcff0cf57d0db932683f292f97086cb84a0ba85a7bce`.
O painel independente pré-geração terminou **2 DEFER, 1 ACCEPT**, recibo
`b92c93f6a08d2fc7db5aedcf6791dbc5935251bd41cd9600bdfd9c036455e13c`.
A objeção material persistiu: ausência na lista local após recarga não prova
exclusão permanente do item no backend. Alguns motivos secundários dos votos
confundem a omissão planejada em C com não equivalência, mas isso não elimina
a objeção principal. O gate de unanimidade não passou. **Nenhuma geração foi
feita para a v2**; o candidato continua fora da contagem de obrigações
executadas.
