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

## 1. Prioridade atual: FPS da execução interativa

- /O1 virou padrão; no workload pareado, mediana foi8,225→8,75 batches/s (+6,4%).
- Mais9 amostras pareadas em8,76 batches/s; continua abaixo do desempenho esperado.
- FTrace mediu99 pedidos de flip/12s (120,6ms por flip), com26,2ms no drain RSX.
- PPU22 RenderThread fez305.628 polls de30µs em12s (9,168s pedidos no wait),
  no loop LR0x000A969C. REA/Rizin no ELF original mostra `func_000A71E4`
  dormindo 30µs enquanto `*(objeto+0xC)[0] != 0`; o branch em0xA720C sai em zero.
- `PPU_WWATCH` atribui stores de1 a `func_000A8E10`/LR0x000A95DC (TID17/22).
  Hook pós-MFC versionado em `patches/0002-post-transfer-spu-watch.patch`.
- Probe combinado20s: 265 GETs SPU4/5 leem status1 + ponteiro0x12805080;
  260 PUTs gravam status0 e preservam o ponteiro; rc=0. PPU escreveu1 260 vezes
  (TID17=36,TID22=224); nenhum negativo observado.
- Correção REA: o wait retorna quando o primeiro word é zero. O PUT SPU que
  gravou0 é compatível com essa saída, mas a identidade entre `*(objeto+0xC)` e
  EA0x106E0900 ainda precisa ser demonstrada. Causa da taxa baixa/tela preta segue
  desconhecida; timeout é bloqueio, não sucesso. Evidence e limites no STATUS.
- Não repetir `PPU_WW_GUARD=1`: armou no ponteiro de inicialização e gerou73.845
  eventos de página. Próximo: seguir a instância e o callback de conclusão com
  PPU_WWATCH/PPU_CASWATCH e o watch pós-DMA; só corrigir semântica provada.
- Para atualizar o SDK usado por FullGame: `tools/build.ps1 -Target Boot` e
  depois `tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4`.
  Depois cruze com jobs/assets e teste se a hipótese explica a tela/FPS.
- A mudança do timer foi compilada corretamente, não mudou a mediana (8,76vs8,75)
  e foi revertida; causalidade do wait com8,3 flips/s ainda não provada.
- Menu/jogo ainda não validados; batches do profiler não são FPS de gameplay.
- Binário /Od preservado em private/build/fifazf_full_debug_baseline.

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

## 3. Ensaiar o avanço real após o novo módulo

- Antes de relink, conferir ausência de processos nativos pais/filhos vivos.
- Rodar os checks afetados e um probe com rótulo novo e configuração revisada.
- Preservar os cinco hashes do perfil e conferir amostras de assets pertinentes.
- Aceite: entrada real do novo módulo observada, resultado/saída registrados;
  próximo bloqueio identificado por bytes/PC, ou novo comportamento verificado.
- Saída 90 continua bloqueio válido; não a converter em sucesso.
- Atualizar checkpoint JSON/STATUS e commitar o incremento autoral validado.

## 4. Próximos marcos do produto

1. Menu e seleção de modo/time/cena no port nativo, usando a referência original já capturada.
2. Cena com jogadores, bola, animação, física e regras originais verificadas.
3. Partida completa, pausa, retorno ao menu, controles e áudio sincronizado.
4. Salvar/retomar progressão, modos offline e matriz de estabilidade/performance.
5. Build e execução reproduzíveis fora da pasta de desenvolvimento.

Só detalhar o marco seguinte quando houver evidência suficiente. Online e melhoria
visual avançada continuam posteriores à base offline funcional.

## Referência do original — concluída para a primeira partida

RPCS3 alcançou uma cena offline com Arsenal × Chicago Fire, 0–0 e relógio visual
2:00. Esse frame é o alvo de comparação para a cena nativa. O frame prova
renderização estática, não controle, movimento, partida completa ou performance.
O processo voltou à biblioteca e os logs estavam vazios; causa desconhecida.
Detalhes e sequência em [`reports/rpcs3-local-reference.json`](../reports/rpcs3-local-reference.json).

## REA e referências externas

Comparação com outros ports: [`docs/recomp-ports-reference.md`](../docs/recomp-ports-reference.md).
REA CLI 6.7.0 + Rizin 0.9.1 já analisaram o ELF por endereço; Evidence ID e
limitações em [`STATUS.md`](../STATUS.md) e
[`reports/performance-opening.json`](../reports/performance-opening.json). REA
MCP está registrado com `REA_RIZIN_COMMAND`; reiniciar Codex para ativá-lo.
