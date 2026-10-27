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

No checkpoint atual, o menu principal original do executável nativo está visível
**e sua navegação foi confirmada**. Inputs mudaram a seleção; Cross abriu o
aviso SIGN IN FAILED; confirmar OK retornou ao menu. Evidência e hashes em
[`menu-renderer-progress.json`](../reports/menu-renderer-progress.json), run
`1793122289140347600`, capturas32/36/46/55/67. Há artefatos gráficos. Arena 3D,
seleção de times e partida não foram validadas. O ensaio foi encerrado
intencionalmente por taskkill (exit1), sem block/crash; não é clean shutdown.
Perfis copiados foram usados e os cinco hashes originais foram preservados.

Não retome o diagnóstico antigo como se o controle ainda estivesse preso no
logo. A prioridade agora é entrar em um modo offline e seguir o próximo
bloqueio real. `Iniciar-FIFA.cmd` / `tools/play.ps1` abre os binários com assets
locais, teclado e perfil interativo separado; ainda não é um pacote autônomo.

## Onde estão código, dependências e evidências

- `src/`: runtime nativo, inicialização, processos, gráficos, input, serviços e diagnósticos.
- `tools/`: extração/lifting, build, probes, inspeção e validação de manifests.
- `tests/`: probes nativos e testes Python/C++; use os checks pertinentes ao código alterado.
- `vendor/ps3recomp/`: SDK externo fixado; não commitar alteração solta nesse submódulo.
- `patches/0001`–`0010`: patches autorais do SDK; o relatório do menu descreve 0005–0010.
- `toolchain.lock.json`: commits e versões fixadas; confira o checkout antes de atualizar algo.
- `private/`: ISO/ELF/assets, executáveis, gerados, perfis, logs e capturas locais; nunca versionar.
- `reports/native-boot-checkpoint.json`: evidência do último ensaio de boot.
- `reports/performance-opening.json`: medições anteriores de abertura.
- `reports/spu-handshake-timing.json`: relógio correlacionado de status PPU, DMA SPU e flips.
- `reports/title-navigation-probe.json`: pacotes válidos sem transição visual.
- `reports/pad-input-consumer.json`: caller `cellPadGetData` e início do parser guest.
- [`references/restreet-reference.md`](references/restreet-reference.md): projeto ReStreet como referência, com limites PS3/Xbox 360.
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

O setup REA aprovado está instalado; esta sessão usou REA CLI 6.7.0 com Rizin
0.9.1. O MCP `open_binary` não aceita o ELF PowerPC, mas `execute-rizin-command`
funciona quando o processo define `REA_RIZIN_COMMAND` para o `rizin.exe` privado
e inclui seu diretório `bin` no PATH. O comando por endereço no callsite de input
retornou Evidence `ev_78025d4611a3c21b91bab08e45f2a20d2c04ce0b6ba216780d61937298af555`.

O ELF reporta headers de programa malformados; os offsets e instruções pontuais
são observações, mas não confie nos limites de função/símbolos automáticos. REA
anteriormente analisou `func_000A71E4` (wait de 30 µs até estado zero),
`func_000A8E10` e o MFC em `sportsrna_spupatch`. Rizin não decodifica SPU aqui;
use lifter e correlação de bytes/hash/runtime para SPU.

## Checkpoint técnico ativo

1. **Menu e input.** Start/Cross foram condicionados por recortes revisados.
   No run363.708s, capturas32/36/46 mostram seleções diferentes;55 mostra
   SIGN IN FAILED;67 confirma retorno ao menu. A correspondência exata entre
   um pulso e uma opção ainda não foi medida; não confundir highlight de
   Practice Arena com entrada nesse modo. O controle não precisa de bypass.
2. **Renderer.** 0005/0006 cobrem16 samplers e bancos SRV disjuntos por frame.
   0009 prioriza a identidade do RT sobre heurísticas de dimensão. 0010 captura
   depth enable/write/compare por draw e o inclui no cache PSO; antes o renderer
   impunha depth ligado em toda a UI. O ensaio intermediário SCREEN_AS_TEX=0
   mostrou gradiente amarelo; com depth correto o menu original ficou visível.
3. **Validação.** Runtime20/20, title probe6/6, série0001–0010 reconstruída e
   conferida, FullGame/O1/SPU relinkado. Quatro probes novos sem PSO FAIL ou
   block/crash;65/65 amostras de assets por ensaio. Hash do executável no relatório.
   Não foi rerodado o gate Boot integral anteriormente interrompido.
4. **Limites do renderer.** Pitch linear guest não é preservado; RT CAB1280×720
   aparece amostrado como2560×720. Há self-sampling sem snapshot e recriação/
   evicção com release antes da submissão potencialmente inseguro. Não resolver
   isso com heurísticas de pixels/dimensões. Capturar pitch/formato por draw.
   Parser inicia depth_func1; o helper usa LEQUAL para esse inválido até receber
   enum GL válido. Stencil/fallback sem guest-FP ainda são parciais.
5. **PPU/SPU anterior.** Preservar handshake/wait e identidades por bytes/hash.
   Evidência em `reports/spu-handshake-timing.json`; 63.2 pedidos de flip/s são
   solicitações, não FPS. Não repetir PPU_WW_GUARD amplo nem converter batches
   em FPS. REA/Rizin por endereço continua disponível conforme seção anterior.

### Próxima investigação recomendada

1. Abrir Hit the Streets offline; usar perfil copiado e capturas antes/depois.
2. Separar seleção apresentada, input consumido e estado lógico. Medir atraso/
   repetição antes de automatizar vários botões rápidos. Verificar teclado físico.
3. Se surgir block90/PC SPU desconhecido, seguir trace e REA/Rizin por endereço;
   não fabricar retornos/status. Se render falhar, isolar o draw e seu estado.
4. Provar seleção de times/cena, jogadores/bola e uma partida offline real.

Build atual: `tools/build.ps1 -Target Runtime`, copiar lib de runtime-clang para
`private/build/boot/sdk/ps3recomp_runtime.lib`, depois `-Target FullGame -SkipLift
-WithSpu`. Sem processos nativos vivos no relink. A verificação de patches usa
worktree temporário para comparar a série inteira quando reverse-check isolado
não é possível. SHA-256 e limites estão no relatório atual, não no hash histórico.

ReStreet é referência de pipeline/produto, mas recompila XEX de Xbox360 via
ReXGlue. Não reutilizar seus binários/patches como dependências do port PS3.
Consulte `docs/references/restreet-reference.md` para comparação concreta.

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
