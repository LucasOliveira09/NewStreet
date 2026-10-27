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

No checkpoint desta revisão, o boot mostrou título e aviso de autosave, e
Start/Cross chegaram ao código original em probes anteriores. Perfil local foi
criado e relido. **Menu navegável, seleção, cena 3D, controle de jogadores,
bola, partida e ciclo completo ainda não foram comprovados.** Não descreva o
projeto como jogável. Janela, pedido de flip ou imagem preta não equivalem a
partida. Uma saída por timeout ou código 90 é falha/bloqueio, nunca sucesso.

## Onde estão código, dependências e evidências

- `src/`: runtime nativo, inicialização, processos, gráficos, input, serviços e diagnósticos.
- `tools/`: extração/lifting, build, probes, inspeção e validação de manifests.
- `tests/`: probes nativos e testes Python/C++; use os checks pertinentes ao código alterado.
- `vendor/ps3recomp/`: SDK externo fixado; não commitar alteração solta nesse submódulo.
- `patches/0001-strict-native-boot.patch`: reprodução de mudanças autorais do SDK.
- `toolchain.lock.json`: commits e versões fixadas; confira o checkout antes de atualizar algo.
- `private/`: ISO/ELF/assets, executáveis, gerados, perfis, logs e capturas locais; nunca versionar.
- `reports/native-boot-checkpoint.json`: evidência do último ensaio de boot.
- `reports/performance-opening.json`: medições de abertura, instrumentação, hashes e limitações.
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
leu 1 e PUT comprometeu 0 nessa EA. O handshake PPU/SPU está provado. O próximo
passo é medir duração e origem do trabalho SPU, mas o PC do log requer cautela:
embora o DMA registre `0x0156C`, esse endereço é NOP na imagem `AssetStream_zlib`
associada à imagem `526190333`. O hook registra `ctx->pc`, que não avança a cada
instrução nos blocos levantados; portanto `0x0156C` não é um call site MFC
provado. IDs, limites e artefatos privados estão em STATUS e
`reports/performance-opening.json`.

## Checkpoint técnico ativo

1. **FPS/espera do RenderThread.** `/O1` é padrão. A comparação de workload
   pareado reporta 8,225 → 8,75 batches/s, mas batches incluem passes offscreen
   e não são FPS visível. Uma medição de abertura separada tem números diferentes
   e não deve ser comparada como pareada. FTrace de abertura registrou 99 pedidos
   de flip em 12 s (mediana 120,6 ms) e drain FIFO RSX de 26,2 ms por intervalo.
   PPU22 (`RenderThread`) registrou 305.628 polls de sleep solicitado de 30 µs
   em 12 s no retorno `0x000A969C`; o estado visto alternou 0/1. A análise
   estática REA/Rizin mostra `func_000A71E4` saindo quando o word apontado por
   `*(objeto+0xC)` é zero, não negativo. Otimização do temporizador foi compilada uma vez,
   não alterou a mediana (8,76 vs 8,75 batches/s) e foi revertida.
2. **Estado do job/asset.** A origem que deve escrever o estado de espera e a
   relação causal com a taxa de flip ainda são desconhecidas. Arquivos
   `genheadtex.big`, `Player_SFX_01.ast`, `TUNA_SFX_BE.ast` e `TUNA_SFX_FE.ast`
   não foram encontrados nos caminhos esperados do disco extraído; impacto no
   estado ou na renderização não foi demonstrado.
3. **Renderização.** Pipeline alcançou criação para shaders de 5.024/5.472 bytes
   no ensaio relatado; uma falha de sampler 4 excede root signature limitada a
   quatro unidades. Há espaços de descritor que se sobrepõem (VP cache 1..96,
   RT 5..20 e base de draw 32). Corrigir o mapeamento real das 16 unidades,
   estado por draw e heaps antes de declarar banco de texturas correto.
4. **Vida útil de recursos.** D3D12 ID 921 indica recurso destruído antes da
   execução do comando e já ocorria no baseline. A aposentadoria precisa seguir
   o fence da submissão efetiva; não aguarde trabalho ainda não enviado.
5. **Captura/jogo.** Última captura posterior a LOADING ficou preta. Várias
   causas continuam possíveis; nenhum vínculo causal foi isolado.

O watch pós-MFC está versionado em `patches/0002-post-transfer-spu-watch.patch`.
Com `SPU_WATCHEA=106E0900` registra `rc`, origem/destino e contador depois da
transferência. `SPU_WATCHEA_EVERY=1` registra todos os hits. Probe combinado de
20 s `private/analysis/runs/1793103246332528600`: MFC GETs de SPU4/5 leram
`1 0x12805080`; PUTs gravaram `0 0x12805080`; 525 registros no total. PPU
`func_000A8E10`, LR `0x000A95DC`, gravou1 260 vezes (TID17=36, TID22=224).
Nenhum valor negativo apareceu. REA/Rizin mostra que `func_000A71E4` dorme 30 µs
enquanto o word em `*(objeto+0xC)` é diferente de zero e sai quando é zero.
No mesmo probe, escritas de cleanup do helper em `0x106E0904/0908` provam que
seu ponteiro era `0x106E0900`; o PPU publicou 1 e o SPU leu 1/gravou 0 nessa
EA. A duração do estado 1 e o impacto na apresentação ainda precisam de medida.
O snapshot runtime `spu-8197-526190333-256.ls` bate nos 25.776 bytes da imagem
fonte (zero diferenças); no mapeamento LS base `0x80`, o word em `0x0156C` é
`00 20 00 00`, NOP. Os blocos gerados em `spu_recomp.c` executam várias
instruções antes de atualizar `ctx->pc`, o que pode deixar o PC reportado pelo
hook defasado dentro de chamadas MFC síncronas. A próxima instrumentação deve
passar o PC guest de `wrch MFC_Cmd` até o hook e registrar os bytes daquela
instrução. REA/Rizin não suporta decodificação SPU neste ambiente; o PC correto
deve ser obtido no lifter/runtime, não inferido do endereço atual do hook.

`PPU_WW_GUARD=1` não deve ser repetido sem condição de armamento melhor: armou
no ponteiro de inicialização e gerou73.845 eventos na página de4 KiB. Use
`PPU_WWATCH`/`PPU_CASWATCH` mais watch pós-MFC. A tentativa com `-Target Runtime`
reconstrói `private/build/runtime-clang`, que FullGame não liga. Para atualizar o
archive compartilhado, execute `tools/build.ps1 -Target Boot` e relinke FullGame.
IDs, contagens, hashes e escopo em
[`performance-opening.json`](../reports/performance-opening.json). Não force
o estado nem burle o wait.

## Próxima investigação recomendada

Siga a prioridade atual em `tasks/plan.md`: corrigir a proveniência do PC do
hook SPU. O snapshot de runtime da imagem `AssetStream_zlib` bate nos 25.776
bytes da fonte; nessa correspondência, `0x0156C` é NOP. Passe o endereço guest
da instrução `wrch MFC_Cmd` pelo lifter até o registro pós-DMA, incluindo a
palavra de instrução. Então atribua semanticamente o job que zera
`0x106E0900`, meça a duração do status e cruze com conclusão de jobs/assets e
chamadas de flip. Preserve a semântica do handshake e do wait.

Depois de duas tentativas sem informação nova, reveja hipótese, pontos de
instrumentação e evidência antes de repetir. Não conclua que o sleep é a causa
só por consumir tempo de CPU. Um teste de throughput deve usar mesmos inputs,
cena, duração e instrumentação; registre mediana/dispersão, hash do binário e
limites do que foi medido. Continue então o caminho real até menu e partida.

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
