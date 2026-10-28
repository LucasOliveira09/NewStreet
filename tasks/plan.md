# Plano ativo do port

Estado/evidência: [checkpoint](../STATUS.md),
[progresso do input e Futsal](../reports/menu-input-progress.json),
[medição limpa do menu](../reports/menu-performance-clean.json) e
[renderização anterior](../reports/menu-renderer-progress.json).
Aceite completo: [prompt](../PROMPT_EXECUCAO_COMPLETA.md).

## 1. Marcos concluídos: menu e fluxo offline inicial

- Renderer: 16 unidades de textura, lookup exato de RT, estado de depth guest.
- Port 0 virtual neutro em `patches/0012`: sem XInput/teclado, eixos em 128.
  O menu deixou de oscilar sozinho: oito capturas estáveis, contra 24
  transições em 25 capturas anteriores sem novo comando.
- Start no título → aviso de autosave → Hit the Streets → Futsal → Select
  Sides → Select Team. Chicago Fire foi marcado READY no lado esquerdo.
- Capturas `frame_41/47/54/61/68/76/82/88` no run `1793124900057646500`.
- O run terminou por timeout em SELECT TEAM, sem block/crash; não é clean exit.
- `Iniciar-FIFA.cmd` abriu janela visível e processo FullGame nativo num teste
  controlado; não valida teclado ou pacote de distribuição.

## 2. Prioridade ativa: atravessar SELECT TEAM e chegar à arena

1. Usar uma nova cópia de `private/userdata` e input guiado por tela revisada.
   Preservar os cinco hashes do save original. `tools/run_title_probe.py`
   automatiza Start e o aviso, mas a seleção posterior exige revisão visual.
2. No SELECT TEAM, escolher o adversário (MLS já selecionada no lado direito),
   avançar a venue/arena e registrar captura antes e depois de cada comando.
3. Validar o primeiro frame 3D, jogadores/bola, resposta ao controle e próximo
   serviço/SPU faltante. Se houver block/crash, seguir PC/bytes via REA/Rizin;
   saída 90 permanece falha, nunca sucesso.
4. Repetir o mesmo fluxo pelo teclado em `Iniciar-FIFA.cmd` e controle físico.
   Validar também voltar, pause, saída, áudio e partida completa.

## 3. Renderização e desempenho ainda abertos

- Os blocos pretos/cinzas e diagonais persistem em menu e match type.
  `patches/0011` passou pitch guest ao D3D12, mas nenhuma textura linear
  suportada nas capturas do menu tinha pitch acolchoado. Não atribuir a ela
  a correção visual; isolar um draw produtor dos blocos.
- Investigar alias: CAB tem RT1280×720 e é lido como textura2560×720;
  examinar pitch de superfície, multisample, remap, alpha/blend e self-sampling.
- `PERF` identificou 124 PSO misses custando 12,94 s no carregamento.
  Sem captura após a 45ª captura (frame_44), o menu ficou em mediana de 21,94
  lotes/s em 30 amostras, zero PSO misses e 82% fora de `render_frame`.
  `patches/0013` distingue lotes/s de chamadas a Present no título da janela;
  o novo run mediu mediana de 22,00 Present/s e 21,69 lotes/s no menu estável,
  sem ganho de desempenho demonstrado. Mapear as seis threads saturadas antes
  de alterar agendamento: a amostra atual não identifica sua função. O ETW
  recusou a captura por política do Windows.
- Aposentar RT/textura referenciados por lista de comandos no fence da
  submissão correta. `wait_for_gpu()` antes do submit não basta.
- Default `depth_func=1` do parser ainda não é enum GL. Stencil, alpha test
  e scissor guest seguem incompletos.

## 4. Build e encerramento de incrementos

- SDK fixado; mudanças autorais reproduzíveis em `patches/0001`–`0013`.
- Runtime: `tools/build.ps1 -Target Runtime`; copiar a lib de runtime-clang
  para `private/build/boot/sdk/ps3recomp_runtime.lib` antes de FullGame.
- Jogo: `tools/build.ps1 -Target FullGame -SkipLift -WithSpu` quando os gerados
  e manifesto já estão atuais; nunca relinkar com pai/filho nativos vivos.
- `tools/apply_patches.py` reconstrói/verifica a série completa.
- Checks proporcionais, revisão do diff, relatório, STATUS/handoff e commit
  local com caminhos explícitos e `git diff --cached --check`.

## 5. Evidência anterior preservada

- Consumo de controle PPU e REA: `reports/pad-input-consumer.json`.
- Handshake PPU/SPU e flips: `reports/spu-handshake-timing.json`; flip não é FPS.
- REA/Rizin e SPU por bytes/faixa/hash estão no checkpoint/histórico.
- ReStreet recompila Xbox360/XEX; é referência, não dependência PS3.
- Marcos seguintes: partida completa → pausa/retorno → save/retomada →
  estabilidade e performance → execução independente da pasta de desenvolvimento.
