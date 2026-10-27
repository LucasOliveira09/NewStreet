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

No checkpoint atual, **o menu estável chega à seleção de times do Futsal**:
Hit the Streets → Futsal → Select Sides → Select Team. Chicago Fire apareceu
READY no lado esquerdo; o adversário ainda não foi escolhido. Evidência,
comandos e hashes em [`menu-input-progress.json`](../reports/menu-input-progress.json),
run `1793124900057646500`, capturas41/47/54/61/68/76/82/88. O ensaio terminou
por timeout de 480 s, sem evento block/crash; não é clean shutdown nem prova
de partida jogável. Blocos e texto incorreto ainda aparecem na interface.
Os cinco hashes do save original permaneceram iguais; probes usam cópias.

Correção essencial: sem XInput e com `PAD_NO_KEYBOARD=1`, o port 0 virtual
enviava analógicos `0,0` (up/left máximos). Antes, 25 capturas sem novo comando
percorreram as cinco opções; depois de `patches/0012`, oito capturas ficaram
em Hit the Streets e um Cross abriu a tela correta. A antiga inferência de que
os pulsos Down explicavam toda a navegação do menu era falsa. Continue a partir
de SELECT TEAM, não do logo. `Iniciar-FIFA.cmd` abriu janela visível em teste,
mas teclado/controle físico e pacote autônomo ainda não foram validados.

## Onde estão código, dependências e evidências

- `src/`: runtime nativo, inicialização, processos, gráficos, input, serviços e diagnósticos.
- `tools/`: extração/lifting, build, probes, inspeção e validação de manifests.
- `tests/`: probes nativos e testes Python/C++; use os checks pertinentes ao código alterado.
- `vendor/ps3recomp/`: SDK externo fixado; não commitar alteração solta nesse submódulo.
- `patches/0001`–`0012`: patches autorais do SDK. 0011 usa pitch de textura;
  0012 centraliza o controle virtual e limpa eixos na desconexão.
- `toolchain.lock.json`: commits e versões fixadas; confira o checkout antes de atualizar algo.
- `private/`: ISO/ELF/assets, executáveis, gerados, perfis, logs e capturas locais; nunca versionar.
- `reports/native-boot-checkpoint.json`: evidência do último ensaio de boot.
- `reports/menu-input-progress.json`: menu estável e caminho Futsal até SELECT TEAM.
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
   `PAD_NO_KEYBOARD=1` deixava o port 0 sem XInput com analógicos0,0;
   `patches/0012` centraliza em128. O run anterior alternou 24 vezes em
   25 capturas sem novo input; o novo ficou oito capturas em Hit the Streets.
   Cross/Down/Cross unitários chegaram a Futsal e SELECT TEAM. Reproduzir o
   trajeto pela sequência de capturas e inputs em `menu-input-progress.json`.
2. **Renderer.** 0005/0006 cobrem16 samplers e bancos SRV disjuntos por frame.
   0009 prioriza a identidade do RT sobre heurísticas de dimensão. 0010 captura
   depth enable/write/compare por draw e o inclui no cache PSO; antes o renderer
   impunha depth ligado em toda a UI. O ensaio intermediário SCREEN_AS_TEX=0
   mostrou gradiente amarelo; com depth correto o menu original ficou visível.
3. **Validação.** Runtime20/20, série0001–0012 reconstruída/conferida,
   FullGame/O1/SPU relinkado. Run final sem block/crash ou erros de parse;
   65/65 amostras de assets iguais à referência. O timeout480 não é clean exit.
   `Iniciar-FIFA.cmd` abriu janela nativa visível; teste encerrado manualmente.
   Hashes e limites no relatório novo. Gate Boot integral não foi rerodado.
4. **Limites do renderer.** 0011 preserva pitch linear guest no upload/cache;
   o manifesto registra o valor. Nas capturas atuais não havia textura linear
   suportada com pitch acolchoado; os blocos persistem. RT CAB1280×720 aparece
   amostrado como2560×720. Há self-sampling sem snapshot e recriação/evicção
   antes da submissão potencialmente insegura. Isolar o draw, sem heurística
   arbitrária de pixels ou dimensão. Houve pico de 12,94s/124 misses de PSO.
   Parser inicia depth_func1; o helper usa LEQUAL para esse inválido até receber
   enum GL válido. Stencil/fallback sem guest-FP ainda são parciais.
5. **PPU/SPU anterior.** Preservar handshake/wait e identidades por bytes/hash.
   Evidência em `reports/spu-handshake-timing.json`; 63.2 pedidos de flip/s são
   solicitações, não FPS. Não repetir PPU_WW_GUARD amplo nem converter batches
   em FPS. REA/Rizin por endereço continua disponível conforme seção anterior.

### Próxima investigação recomendada

1. Retomar em SELECT TEAM: escolher adversário, avançar venue/arena com perfil
   copiado e capturas antes/depois. O lado esquerdo Chicago Fire já ficou READY.
2. Verificar o mesmo caminho com teclado/controle físico no launcher; medir
   FPS apresentado sem RSX_CAP contínuo e isolar os blocos do menu por draw.
3. Se surgir block90/PC SPU desconhecido, seguir trace e REA/Rizin por endereço;
   não fabricar retornos/status. Se render falhar, isolar o draw e seu estado.
4. Provar arena, jogadores/bola, comandos e uma partida offline real.

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
