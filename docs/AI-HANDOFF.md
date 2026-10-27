# Guia de retomada para agentes — FIFA Street nativo

Atualizado em 27/10/2026. Este arquivo é o mapa de entrada para uma nova IA.
Ele não substitui as instruções, o aceite nem os dados privados do jogo.

## Leia nesta ordem

1. [`../AGENTS.md`](../AGENTS.md): limites de segurança, evidência, build e Git.
2. [`../STATUS.md`](../STATUS.md): checkpoint curto; substitua-o ao concluir um incremento.
3. [`../tasks/plan.md`](../tasks/plan.md): próxima etapa ativa e marcos do produto.
4. [`../PROMPT_EXECUCAO_COMPLETA.md`](../PROMPT_EXECUCAO_COMPLETA.md): objetivo integral e aceite final.
5. O relatório indicado pela etapa e o código específico que será alterado.

Não carregue todo `docs/history/`, `private/`, os arquivos gerados ou o prompt
integral em toda sessão. Consulte o índice de [`history`](history/README.md) e
busque apenas o assunto necessário. `private/` contém entradas e evidências
derivadas do disco local; ele é ignorado pelo Git por projeto.

## Objetivo e critério de verdade

Reconstruir FIFA Street 2012 PS3 BLUS30882 1.00 como aplicação Windows x64
nativa, sem RPCS3/Xenia e sem trocar silenciosamente a recompilação por
interpretador/JIT. O usuário autorizou continuar até alcançar partida jogável.
O aceite completo está no prompt de execução; os próximos marcos estão no plano.

No checkpoint desta revisão, o executável nativo mostra o logo FIFA STREET em
1280×720. Um probe envia START/CROSS/DOWN como pacotes `cellPadGetData` válidos
a memória guest, mas a imagem não muda. Isso não prova consumo/aceitação pelo
jogo. Perfil de probe foi copiado e os saves originais foram preservados.
**Menu navegável, seleção, cena 3D, controles, bola e partida não estão comprovados.** Não descreva o
projeto como jogável. Janela, pedido de flip ou imagem preta não equivalem a
partida. Uma saída por timeout ou código 90 é falha/bloqueio, nunca sucesso.

## Onde estão código, dependências e evidências

- `src/`: runtime nativo, inicialização, processos, gráficos, input, serviços e diagnósticos.
- `tools/`: extração/lifting, build, probes, inspeção e validação de manifests.
- `tests/`: probes nativos e testes Python/C++; use os checks pertinentes ao código alterado.
- `vendor/ps3recomp/`: SDK externo fixado; não commitar alteração solta nesse submódulo.
- `patches/0001-strict-native-boot.patch` e `patches/0002`–`0004`: reprodução dos patches autorais do SDK.
- `toolchain.lock.json`: commits e versões fixadas; confira o checkout antes de atualizar algo.
- `private/`: ISO/ELF/assets, executáveis, gerados, perfis, logs e capturas locais; nunca versionar.
- `reports/native-boot-checkpoint.json`: evidência do último ensaio de boot.
- `reports/performance-opening.json`: medições anteriores de abertura.
- `reports/spu-handshake-timing.json`: relógio correlacionado de status PPU, DMA SPU e flips.
- `reports/title-navigation-probe.json`: pacotes de controle válidos sem mudança visual.
- `reports/rpcs3-local-reference.json`: configuração observada do RPCS3 local, gravação de referência e procedimento para capturar a navegação após Start.
- [`recomp-ports-reference.md`](recomp-ports-reference.md): comparação de ReStreet e ports PS3 em `ps3recomp`, com implicações para SPURS/render.
- `docs/history/`: checkpoints antigos preservados; podem estar desatualizados.

Os identificadores de guest como `0x000A969C` são endereços observados, não
nomes semânticos. Contagens de funções, wrappers ou registros SPU não provam
que os serviços ou algoritmos estejam completos. Para associar uma rotina SPU,
registre bytes/faixa/hash e evidência da entrada observada; preserve limites de
código, constantes, stops e PCs de retorno.

## Como reproduzir build e observação

O script de build valida o commit do submódulo, reaplica o patch versionado,
usa Visual Studio x64, LLVM privado e CMake/Ninja do Visual Studio. As entradas
privadas da toolchain e do jogo precisam existir localmente.

```powershell
Set-Location D:\Ludevi\projetos\fifa-street-native
git status --short
git branch --show-current
git rev-parse HEAD
private\python-env\Scripts\python.exe tools\check_agent_setup.py
./tools/build.ps1 -Target Boot
./tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4
```

`-SkipLift` só é válido quando os arquivos gerados correspondem às entradas e
ao manifesto atuais; caso contrário, faça lifting. O manifesto SPU deve estar
atualizado antes de FullGame. Para diagnóstico sem otimização, use
`-DebugFullGame`; FullGame usa `/O1` por padrão. O resultado em
`private/build/fifazf_full/` é o binário da sessão de desenvolvimento, ainda
dependente dos ELF/disco conforme os argumentos de runtime; não é instalador
autônomo pronto para distribuição.

`tools/run_native.py` produz um probe controlado (`--profile startup|full`,
`--timeout`, `--direct`, rastreio/captura/observação de assets). Para uma ação
de botão condicionada por tela, use `tools/run_title_probe.py`: referências de
captura devem ser inspecionadas previamente e cada entrada deve ser autorizada
por uma tela/ROI revisada. Um botão enviado não prova que o jogo o aceitou;
inspecione o estado seguinte e os artefatos do run. Nunca reaproveite um label
como se fosse nova evidência.

Antes de relink ou iniciar outra execução, confira que o processo nativo e seus
filhos encerraram. Não basta o launcher sair. Ao ler log vivo, leia intervalos
limitados de bytes; não use `Get-Content -Tail` em stderr aberto. Não substitua
o perfil de save para facilitar probes: compare os cinco hashes do checkpoint.
Probes diretos precisam definir `PS3_HDD0_ROOT` e `PS3_HDD1_ROOT` para
`private/userdata/dev_hdd0` e `private/userdata/dev_hdd1`; o lançamento de memória
registrado abaixo omitiu essas variáveis e criou `gamedata/trophies/` na raiz.
Esse conteúdo foi mantido e a pasta está ignorada pelo Git.

### Referência externa no RPCS3

O RPCS3 portátil local usa Vulkan e XInput e carrega BLUS30882 por ISO. A gravação
disponível termina no título `PRESS START BUTTON`; ela não registra navegação.
Para comparar o comportamento original, siga o procedimento em
[`rpcs3-local-reference.json`](../reports/rpcs3-local-reference.json). O RPCS3
serve como referência do original, não como evidência de avanço do port nativo.
Na execução informada em 27/10, o usuário chegou a uma partida; a biblioteca
depois mostrou última execução 09:49 e 22min55s acumulados. A inspeção da tela
09:51 já encontrou a biblioteca, sem nova gravação/captura ou log. Trate a
entrada em partida como relato do usuário até haver evidência visual; não use o
rótulo geral `Ingame` da lista de compatibilidade como prova desta execução.

Uma captura posterior confirmou o boot até a cena offline Arsenal × Chicago Fire,
com HUD e 3D visíveis. A captura é `private/analysis/rpcs3_reference/live-match-current.png`;
detalhes e limites estão no relatório estruturado e no documento de referências.

### REA

O projeto contém `tools/rea.ps1` e REA CLI 6.7.0. Setup registrou o MCP Codex
e instalou a skill global versão42/207 ferramentas. Rizin estático 0.9.1 fica
em `private/toolchain/`; `REA_RIZIN_COMMAND` está configurado na entrada MCP,
mas reinicie Codex para carregar o ambiente. Ghidra Windows P0 não aceita este
ELF PowerPC; Hopper não suporta Windows. O REA CLI analisou `FIFAZF.elf`, SHA-256
`5521a262…be34afb`: o disassembly de `0xA71E4` mostra poll de 30 µs até o status
ser zero. Evidence completa (privada/ignorada):
`private/analysis/rea/rea-fifazf-wait.json`, ID
`ev_61b45e6f394c696b71e944869e2130639021b4eb0d82dc5addc95e6512bb755b`.
Rizin avisou que três program headers são inválidos e a análise automática
agrupou rotinas próximas; use apenas as instruções por endereço até validar
limites de função. `pdc` não devolveu pseudocódigo. Análises também cobriram
`func_000A8E10` (escreve 1 em `*(contexto+0xC)`) e `func_000A9680` (passa
`*(objeto+0x9C)` ao helper). O log do mesmo run mostra o helper escrevendo em
`0x106E0904/0908`, comprovando que seu `*(objeto+0xC)` era `0x106E0900`; SPU GET
leu 1 e PUT comprometeu 0 nessa EA. O handshake PPU/SPU está provado. A proveniência do MFC também foi fechada:
`patches/0003-spu-wrch-callsite-pc.patch` preserva o PC guest em cada `wrch
MFC_Cmd`; no run `1793110334315435500`, `0x015DC` (`21 A0 0A 8B`) mapeia para
o overlay residente `sportsrna_spupatch` (ID `592606456`, SHA-256
`35274f8f…22aeeae`). O GET passa pelo LR `0x1408`, e o PUT pelo LR `0x14F0`.
O ID `526190333` é identidade do contexto SPU, não do overlay residente. O
snapshot antigo que confere com `AssetStream_zlib` caracteriza apenas aquele
snapshot estático; ele não localiza o código do probe atual. A rotina baixa de
transferência está atribuída, mas a finalidade do job superior, sua duração e
a relação causal com flips continuam em aberto. IDs, logs e limites estão em
STATUS e `reports/performance-opening.json`.

## Checkpoint técnico ativo

1. **Input e navegação.** Run `1793112938625277900` usou cópia do perfil e
   `PAD_ALWAYS_CHANGE=1`, `PAD_REPORT_TRACE=1`, `PAD_SCRIPT='4:0x0008,7:0x4000,10:0x0040'`.
   Seis transições válidas (`len=20`, `mode=122`) foram escritas em
   `0xD0189CE0`; oito capturas tiveram o mesmo hash e mostram o logo. É prova de
   entrega ao buffer guest pelo HLE, não de consumo pelo código de UI. O próximo
   passo é descobrir quem lê esse endereço e qual estado controla a transição.
   Evidência/limitações em [`title-navigation-probe.json`](../reports/title-navigation-probe.json).
2. **Handshaking e flips.** Run direto `1793111736649624200`, trace de 12 s:
   472 pedidos de flip, mediana 15.8 ms (63.2 solicitações/s, não FPS visível),
   237 stores de status 1 e 236 MFC GET/PUT de status. Correlação aproximada por
   ordem encontrou 236 ciclos; não há ID do job e causalidade não está provada.
   Ver [`spu-handshake-timing.json`](../reports/spu-handshake-timing.json).
3. **Identidade do MFC.** `wrch MFC_Cmd` em `sportsrna_spupatch`, PC `0x015DC`,
   bytes `21 A0 0A 8B`, overlay residente ID `592606456`; GET retorna por LR
   `0x1408`, PUT por `0x14F0`. O contexto SPU `526190333` não é ID do overlay.
   O significado do job superior permanece desconhecido.
4. **Desempenho.** `/O1` é padrão. Medição pareada anterior foi 8.225 → 8.75
   batches/s; são batches incluindo passes offscreen, não FPS. A alteração de
   timer não teve ganho e foi revertida.
5. **Renderização.** Sampler 4 excede root signature limitada a quatro unidades;
   bancos de descritores ainda se sobrepõem. D3D12 ID 921 indica recurso
   destruído antes de Execute; aposentar pelo fence efetivamente submetido.
   Uma captura após LOADING ficou preta; causa não isolada.

`func_000A71E4` faz poll de 30 µs e sai quando o word em `*(objeto+0xC)` é zero.
`func_000A8E10` publica 1 em `0x106E0900`; o SPU lê 1 e grava 0. Preservar o
handshake/wait até provar semântica superior. Não repetir `PPU_WW_GUARD=1`:
armou cedo e gerou 73.845 eventos na página de 4 KiB. Use watch estreito.

O conjunto versionado de patches vai até `0004-ppu-status-watch-timestamp.patch`.
`python tools/apply_patches.py` reconheceu 0001–0004 aplicados. O gate
`tools/build.ps1 -Target Boot` ficou preso em `check_switch_lowering.py` e foi
cancelado; ele não foi aprovado nesta revisão. CMake direto reconstruiu o target
`fifa_boot`, os 48 testes `test_boot_diagnostics.py` passaram, e o relink
`tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4` concluiu. SHA-256
do FullGame: `C9D2CBA494E2B47D44B5339728AB50A3E6FF6927D7DB69EF9B8EFE6002A6C99D`.

### Próxima investigação recomendada

1. Instrumentar `cellPadGetData` para registrar LR/TID do PPU no mesmo evento que
   o payload, como patch composável com o estado atual de `0001`; usar LR para
   localizar o chamador no `FIFAZF.elf` e confirmar quais buffers/rotinas leem.
2. Comparar o código que interpreta o relatório com a implementação de
   `cellPadGetData`, modo/pressão, configuração de porta e eventos de UI. Só
   trocar semântica depois de evidência, sem inventar estado de menu.
3. Repetir uma ação autorizada pela tela e capturar o estado seguinte. Aceite é
   mudança visual/estado comprovada e navegação reproduzível, não pacote escrito.
4. Depois voltar aos bloqueios de renderização e alcançar uma partida offline.

REA MCP não abriu esse ELF nesta sessão por limitação de arquitetura. Use o REA
CLI/Rizin já configurado quando o provider local estiver acessível; identifique
primeiro por que a chamada CLI retornou `ERR_REA_WINDOWS_NATIVE`. Rizin não
interpreta SPU aqui; preserve bytes, faixa, hash, PC e logs runtime.

## Registrar cada incremento para a próxima IA

Ao fechar um incremento técnico:

1. Relacione a pergunta, hipótese e evidência anterior que justificaram a mudança.
2. Registre arquivos/código alterados, comando exato e configuração/hash do build.
3. Guarde logs, capturas, JSON e dumps grandes em `private/`; versione apenas
   scripts, manifests e relatórios sem material proprietário.
4. Marque o resultado como confirmado, rejeitado ou inconclusivo; cite limitações.
5. Atualize `STATUS.md` (60–100 linhas, estado atual) e o item ativo do plano.
   Use `reports/` para resultados estruturados; não transforme STATUS em diário.
6. Revise `git diff`, faça os checks pertinentes, `git diff --cached --check`,
   adicione caminhos explícitos e crie commit local pequeno. Não publique remoto.
7. Deixe o próximo passo executável, incluindo arquivos/funções e critério de
   parada/aceite. Se a hipótese mudar, documente o porquê e mantenha dados antigos.

## Não fazer

- Não preencher retornos de serviço, status CELL ou resultados para passar boot.
- Não apagar ou sobrescrever saves privados; não commitar código/ativos derivados.
- Não chamar um teste unitário de rotina de prova de algoritmo completo.
- Não afirmar compatibilidade ampla por um único boot, menu ou cena sintética.
- Não alterar SDK sem patch reproduzível e validação correspondente.
- Não commitar até conferir os arquivos staged e as alterações preexistentes.
