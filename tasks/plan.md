# Plano ativo do port

Estado e evidências atuais: [checkpoint](../STATUS.md).
Objetivo e aceite integral: [prompt completo](../PROMPT_EXECUCAO_COMPLETA.md).
Histórico preservado: [índice](../docs/history/README.md).

## Etapas concluídas neste incremento

- Identificador não associa rótulos fora dos limites; dez regressões autorais passaram.
- Imagem 0x1ee9580 traduzida: 173 entradas; CRT/BSS e dez construtores validados.
- Entradas reais de 0x1ee9580 e Replay_matrixsave observadas; perfil preservado.
- Replay_matrixsave: 78 entradas, CRT vazio e guardas validados.
- Replay_matrixload: 189 entradas, BSS/construtor e constantes validados; entrada real.
- FIFARNA batchplayer pass0: 477 entradas, BSS448 e dois construtores validados; entrada real.
- Railtracks path estimates: 1.769 entradas, CRT/BSS25072/4ctors e cauda stop0 validados; entrada real.
- User music arbiter: init PIC4bases e 4.096 amostras DSP conferidas contra oráculo; entrada real.
- Compressor1: 114 entradas, init PIC4bases/callbacks/contexto/guardas validados; entrada real.
- Reverb1: 287 entradas, init PIC4bases/contexto/32bytes de estado preservados; entrada real.
- Matrix panner: 26 entradas, init PIC4bases/callbacks/guardas validados; entrada real.
- Delay: 96 entradas, init PIC4bases/callbacks/contexto/guardas validados; entrada real.
- Lote4 DSPs: 16 posições de init validadas; ReverbIR1 entrou, outros3 ainda não observados.
- 144 testes do projeto, 46 Boot e 65 amostras de assets passaram.

## 1. Prioridade atual: provar consumo do controle e navegar o menu

- Probe direto `1793112938625277900`, com cópia do save: `PAD_SCRIPT` enviou
  START (`0x0008`), CROSS (`0x4000`) e DOWN (`0x0040`). `PAD_REPORT_TRACE`
  observou seis transições válidas (`len=20`, `mode=122`) em `0xD0189CE0`.
- Oito amostras capturadas tiveram o mesmo hash e mostram o logo. O follow-up
  prova que o guest lê `len` e o word de botões, mas não que a ação alcance a UI.
  Probes terminaram por timeout.
- `PAD_ALWAYS_CHANGE=1` foi somente diagnóstico e muda a cadência de relatórios.
  Não assuma que esse modo ou os botões causem avanço do menu.
- O callsite está identificado: NID `0x8B72CDA1`, LR `0x014351D0`; REA mostra
  `bl 0x01C0F17C` em `0x014351CC`, com `SP+0x70` como buffer. Depois o game lê
  len em `SP+0x70`, verifica o word de botões em `SP+0x78` e chama `0x01434DB8`.
  Esse helper atualiza o bitset digital ou array de pressão do dispositivo guest.
  REA também traçou sampler `0x011AA178` e dispatcher de vínculos `0x011A9EE0`;
  a fixture cobre somente metadados autorais. IDs/logs/limitações em
  `reports/pad-input-consumer.json`.
- Próximo: capturar controles e metadados reais, seguir o valor lógico até o
  consumidor de UI. Conferir `SetPortSetting(0x4, 0x2)` e layout do relatório.
  Aceite: mudança de tela reproduzível; pacote lido/normalizado não basta.
- O MCP REA `open_binary` rejeita ELF PowerPC. A CLI/Rizin funciona com
  `REA_RIZIN_COMMAND` e PATH explícitos. Evidence/limitações em STATUS e no
  relatório do callsite.

### Handshake e medição de abertura já registrados

- O wait `func_000A71E4` sai quando `*(objeto+0xC)[0] == 0`. PPU publica 1 em
  `0x106E0900` via `func_000A8E10`; MFC GET lê1 e PUT grava0.
- MFC exato: `sportsrna_spupatch`, PC `0x015DC`, bytes `21 A0 0A 8B`, overlay
  residente ID `592606456`; LR GET `0x1408`, LR PUT `0x14F0`. Semântica do job
  superior ainda desconhecida.
- Run `1793111736649624200`: FTrace de 12 s, 472 pedidos de flip (mediana
  15.8 ms; 63.2 pedidos/s, não FPS visível), 237 stores de status1, 236 GET e
  236 PUT. Correlação por eventos próximos sugere 236 ciclos; não há job ID nem
  causalidade provada. Relatório `reports/spu-handshake-timing.json`.
- Não repetir `PPU_WW_GUARD=1`: armou cedo e gerou73.845 eventos numa página de
  4 KiB. Não forçar status nem contornar o wait.
- `/O1` segue padrão: 8.225→8.75 batches/s no workload pareado. Batches não são
  FPS. Otimização de timer sem ganho foi revertida.
- Build mais recente: CMake direto atualizou `fifa_boot`; 48 diagnósticos Boot
  passaram; FullGame relinkado com `tools/build.ps1 -Target FullGame -SkipLift
  -WithSpu -Jobs 4`. O gate `tools/build.ps1 -Target Boot` travou em
  `check_switch_lowering.py` e foi cancelado; não contar como sucesso.

## 2. Banco real de16texturas e retirement de recursos

- FP completo/snapshot por draw concluído; zerocompilefail no ensaio180s,
  programas5024/5472bytes compilaram. Literal/hash/constantes agora coerentes.
- Falha atual: sampler4 fora da root signature. Mapear16unidades em estado,
  SRVs/samplers, cubemaps, heaps, strides e descritores ausentes.
- Espaços atuais se sobrepõem (VPcache1..96, RT5..20, draw32+); tornar disjuntos
  e reservar bancos de descritores por frame com testes de exclusividade/limites.
- ID3D12Resource foi destruído antes Execute (ID921) já no baseline. Retirar
  texturas/RTs apenas após fence de submissão, sem aguardar trabalho ainda não enviado.
- 18 runtime/48 Boot/146 projeto passaram; revisão FP sem pendências.
- Menu navegável e gameplay ainda não validados; continuar até próximos marcos.

## 3. Confirmar navegação real após correção comprovada

- Preserve os cinco hashes do save original; probes usam perfil copiado e raízes
  HDD0/HDD1 explícitas.
- Rode build/checks afetados e um probe com label novo. Registre input, caller LR,
  TID, buffer/bytes, frame anterior e frame seguinte; timeout segue sendo bloqueio.
- Aceite: entrada dirigida pela tela e transição reproduzível, com captura
  revisada. Não considerar pacote escrito, window, flip ou logo como progresso
  de navegação.
- Atualize relatório, checkpoint, handoff e commit local pequeno após revisar o
  staging. Não publicar remoto.

## 4. Próximos marcos do produto

1. Menu e seleção de modo/time/cena no port nativo, usando a referência original já capturada.
2. Cena com jogadores, bola, animação, física e regras originais verificadas.
3. Partida completa, pausa, retorno ao menu, controles e áudio sincronizado.
4. Salvar/retomar progressão, modos offline e matriz de estabilidade/performance.
5. Build e execução reproduzíveis fora da pasta de desenvolvimento.

Só detalhar o marco seguinte quando houver evidência suficiente. Online e melhoria
visual avançada continuam posteriores à base offline funcional. A referência
externa ReStreet está analisada em [`docs/references/restreet-reference.md`](../docs/references/restreet-reference.md); é port Xbox 360/ReXGlue, não dependência para PS3.

## Referência do original — concluída para a primeira partida

RPCS3 alcançou uma cena offline com Arsenal × Chicago Fire, 0–0 e relógio visual
2:00. Esse frame é o alvo de comparação para a cena nativa. O frame prova
renderização estática, não controle, movimento, partida completa ou performance.
O processo voltou à biblioteca e os logs estavam vazios; causa desconhecida.
Detalhes e sequência em [`reports/rpcs3-local-reference.json`](../reports/rpcs3-local-reference.json).

## REA e referências externas

REA CLI 6.7.0 + Rizin 0.9.1 analisaram instruções por endereço; MCP `open_binary`
rejeita ELF PowerPC. Para CLI, definir `REA_RIZIN_COMMAND` e PATH para o Rizin
privado. Evidence de callsite e limitações em [`reports/pad-input-consumer.json`](../reports/pad-input-consumer.json)
e [`STATUS.md`](../STATUS.md). Rizin avisa sobre headers inválidos e não decodifica
SPU; manter análise pontual e usar o lifter para SPU.

A referência [ReStreet](https://github.com/samuelit0davila/fifa-street-pc-port)
é Xbox 360/ReXGlue, não dependência do port PS3. Resumo, diferenças e trilhas
para inspeção em [`docs/references/restreet-reference.md`](../docs/references/restreet-reference.md).
