# Checkpoint atual — 27/10/2026

Alvo: FIFA Street 2012 PS3 BLUS30882 1.00 → Windows x64 nativo.
Branch: `codex/ps3-native-bootstrap`. Incremento: protocolo do estado de espera do RenderThread.
Guia de retomada: `docs/AI-HANDOFF.md`. Evidência estruturada: `reports/performance-opening.json`.

## Critério de verdade

O boot mostra título e aviso de autosave. Start/Cross chegaram ao código original em probes anteriores; o perfil local foi criado e relido. **Menu navegável, seleção, cena 3D, controle, bola, partida e ciclo completo continuam sem validação.** Timeout, janela ou flip não significam jogo jogável. O objetivo autorizado é chegar a uma partida offline completa no Windows.

## Novo diagnóstico do wait

- PPU22 (`RenderThread`) gastou 9,168 s de 12 s em 305.628 chamadas `sys_timer_usleep(30us)` no loop chamado em `LR 0x000A969C`; helper `func_000A71E4` lê o primeiro word de `*(objeto+0xC)` e só sai se o valor for negativo.
- Watch pós-transferência foi adicionado ao SDK por `patches/0002-post-transfer-spu-watch.patch`. `SPU_WATCHEA=<EA>` agora conta hits e registra depois do MFC, com resultado e bytes de origem/destino. `SPU_WATCHEA_EVERY=1` captura todos.
- Probe combinado de 20 s: `private/analysis/runs/1793103246332528600`. PPU escreveu `1` em `0x106E0900` 260 vezes: TID17=36, TID22=224, sempre `func_000A8E10`, caller LR `0x000A95DC`. Inicialização também escreveu zeros e ponteiros.
- No mesmo probe, SPU4/5 fez 265 GETs de 8 bytes (primeiro word `1`, segundo `0x12805080`) e 260 PUTs (primeiro word `0`, segundo `0x12805080`), todos `rc=0`, PC reportado `0x0156C`, imagem `526190333`. O destino do PUT correspondeu aos bytes registrados depois da execução.
- Não foi observado estado negativo. O SPU alternar `1→0` e o PPU escrever `1` está confirmado; o significado do ponteiro, a rotina que deveria concluir o wait e a relação com a tela preta ainda não estão provados. Não force sinal nem burle o loop.
- A tentativa anterior com `-Target Runtime` recompilou outra biblioteca e não atualizou o FullGame. Para este executável, use `-Target Boot` para reconstruir `private/build/boot/sdk/ps3recomp_runtime.lib`, depois relinke FullGame.
- `-Target Runtime`: build concluído, 18/18 checks passaram. `-Target Boot`: build concluído, 48/48 checks passaram. FullGame relinkado após ambos os ajustes.
- Probes normais EBOOT→FIFAZF de 35 s, 20 s, 20 s e 15 s terminaram por timeout; o último capturou348 DMAs com contagem atômica. Nenhum prova avanço de menu.
- A page guard anterior foi armada cedo no ponteiro `0x106E0800` e produziu 73.845 registros na página de 4 KiB. Não repetir sem um armamento condicionado ao valor certo; o watch pós-DMA e `PPU_WWATCH` são mais estreitos.

## Outros bloqueios ativos

- Desempenho de abertura: /O1 teve 8,75 batches/s contra 8,225 no trecho pareado; batches não são FPS visível. FTrace: 99 flips/12 s, mediana 120,6 ms; drain RSX 26,2 ms.
- A alteração de temporizador não mudou a mediana (8,76 vs 8,75 batches/s) e foi revertida.
- Última captura após LOADING é preta. Sampler4 excede root signature limitada a quatro unidades; mapa real tem sobreposições de descritores. D3D12 ID921 acusa recurso destruído antes do Execute.
- Alguns assets pedidos no boot não existem nos caminhos extraídos. O impacto ainda não foi isolado.
- Guardar os cinco hashes do save conforme `reports/native-boot-checkpoint.json`. Nunca substituir o perfil.

## Base já validada neste port

- FullGame compila 99 mil funções PPU do FIFAZF, além de workloads SPU levantados; EBOOT é reproduzido separadamente e inicia o ELF do jogo pelo launcher nativo.
- Builds de desenvolvimento exigem as entradas privadas e a toolchain fixada. `-SkipLift` só vale quando os artefatos gerados correspondem aos ELFs e manifests atuais.
- `tools/run_native.py --profile full --timeout N` grava logs e `result.json` sob `private/analysis/runs`; timeout mata pai e descendentes e não declara sucesso.
- Probes usuais preservam os saves em `private/userdata`; conferir os cinco hashes de `reports/native-boot-checkpoint.json` antes/depois.
- O teste pareado de /O1 mede batches de renderer, incluindo passes fora da tela. Não converter esse dado em FPS do jogo.
- Foram identificadas entradas reais e testadas em módulos de AI, Replay, Railtracks e áudio. Esses resultados cobrem entradas/construtores/callbacks descritos no plano, não provam algoritmos completos.
- O relatório de desempenho guarda os hashes exatos do executável FullGame e do archive Runtime usado nesta revisão.
- O lift SPU preserva PC de retorno a stops originais; imagens e limites precisam continuar vinculados a bytes/hash, sem usar rótulo inferido como nome original.
- Renderer D3D12 ainda requer mapeamento comprovado de 16 texturas/samplers, descritores disjuntos e aposentadoria de recursos pelo fence efetivamente submetido.
- Arquivos privados de jogo, ELF, assets, executáveis, logs e capturas ficam em `private/`; não versionar conteúdo derivado nem saves.

## Referência local no RPCS3

- RPCS3 portátil `v0.0.43-20387-aa9ebd2f`, Vulkan, RX 580 2048SP, 1280x720, XInput. FIFA Street BLUS30882 está registrado como ISO externa; não está instalado em `dev_hdd0/game`.
- A gravação existente de 18,88 s mostra o splash e depois `PRESS START BUTTON`; Start não foi pressionado e nenhum menu foi observado. A sessão inspecionada estava ociosa na tela de boas-vindas; logs estavam vazios.
- Configuração, perfil e saves não foram alterados. Referência, limites e procedimento para o próximo run: [`reports/rpcs3-local-reference.json`](reports/rpcs3-local-reference.json).
- Próxima coleta depende do usuário: abrir BLUS30882, pressionar Start uma vez, registrar a transição ou 10–20 s sem mudança, e fechar RPCS3 normalmente para liberar os logs.
- Nova execução em 27/10: o usuário relata ter entrado em uma partida; lista do RPCS3 mostra última execução 09:49 e 22min55s acumulados. Na inspeção 09:51, emulador já estava de volta à biblioteca. Nenhum vídeo/captura novo ou log disponível, então gameplay/FPS ainda sem evidência visual; detalhes em `reports/rpcs3-local-reference.json`.
- Inspeção ao vivo 09:55: a janela de renderização está ativa/responsiva, mas exibe `Applying PPU Code...`, módulo284/284, estimativa22m. Duas capturas com10s de intervalo não mudaram essa tela. Título do RPCS3 oscilou28,71→58,04→58,01 FPS; isso é tela de carregamento, não FPS de partida. Log continua zerado; capturas privadas e métricas estão no relatório.
- Acompanhamento 09:58–09:59: avançou para o aviso de autosave e depois `Hit the Streets — Select Sides`. Controle está no lado vermelho; o prompt mostra `Cross: Advance`; a barra online avisa desconexão dos servidores EA. A tela ficou igual por30s aguardando botão. Janela responsiva, título ~29,8–30 FPS; esse valor é do menu, não gameplay. Capturas/linha do tempo em `reports/rpcs3-local-reference.json`.
- 10:00:51 avançou a `Select Team`; categoria Barclays PL e Inglaterra destacadas, nome do clube ainda `---`. Prompt é `Cross: Select`; quadro seguinte 10:01:22 permaneceu igual. Título variou33,28→51,34 FPS, leitura de menu, não desempenho de partida.
- 10:03:32: captura ao vivo confirma partida offline Arsenal × Chicago Fire, 0–0 e relógio 2:00; renderiza quadra, jogadores, bola e HUD. Barra de título marcou 45,58 antes e 57,32 no quadro; é leitura instantânea. Às10:03:56, RPCS3 retornou à biblioteca, última execução10:03, tempo acumulado32m52s. Não há log para determinar se foi saída normal ou inesperada; partida completa/controles/FPS sustentado não comprovados. Evidência privada no relatório.

## Reproduzir a validação do incremento

- `private\python-env\Scripts\python.exe tools/apply_patches.py` reconhece os patches 0001 e 0002 já aplicados no checkout fixado.
- `tools/build.ps1 -Target Runtime`: biblioteca de runtime alternativa; 18 checks passaram, mas esse archive não é consumido pelo FullGame.
- `tools/build.ps1 -Target Boot`: atualizou `private/build/boot/sdk/ps3recomp_runtime.lib`; 48 checks passaram.
- `tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4`: relinkou `private/build/fifazf_full/fifa_boot.exe` com o archive de Boot atualizado.
- `SPU_WATCHEA=106E0900`, `SPU_WATCHEA_EVERY=1`, `PPU_WWATCH=106E0900`, `PPU_WWATCH_LEN=0x10`, `PPU_WWATCH_MAX=0` foram usados somente no probe instrumentado de 20 s.
- Todos os quatro probes desta etapa encerraram por timeout; não houve captura gráfica nem validação de menu/jogo.

## Próximo trabalho

1. Partir dos argumentos/campos do objeto passado por `func_000A9680 → func_000A71E4` e do publicador chamado por `func_000A8E10`; identificar o worker/callback responsável pelo sinal terminal negativo.
2. Instrumentar os campos dessa mesma instância com `PPU_WWATCH`/`PPU_CASWATCH` e watch pós-MFC. Correlacionar pedido, job SPU, retorno e estado final; distinguir instâncias de TID17 e TID22.
3. Corrigir somente a semântica/comunicação que a evidência demonstrar. Reproduzir probe normal e verificar se o RenderThread progride além do wait e se surge uma tela verificável.
4. Em seguida atacar a captura preta, banco de 16 texturas/descritores e retirement por fence; voltar ao caminho de menu e partida offline.

Probes diretos devem definir `PS3_HDD0_ROOT` e `PS3_HDD1_ROOT` para `private/userdata/dev_hdd0` e `.../dev_hdd1`. A pasta local `gamedata/` permanece ignorada e preservada.
