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
  no loop LR0x000A969C. Estado observado0/1; o laço termina ao ler valor negativo.
- `PPU_WWATCH` atribui stores de1 a `func_000A8E10`/LR0x000A95DC (TID17/22).
  SPU4/5 pedem MFC_GET 0x40 e MFC_PUT 0x20 de8 bytes para EA0x106E0900,
  LS0x3ED10, PC0x156C. O watch atual roda antes da execução; valor gravado não provado.
- 315 snapshots read-only a cada25ms viram status0/1, nenhum negativo. Não exclui
  transiente entre leituras; `SPU_WATCHEA` não prova o PUT. Timeout segue bloqueio.
- Próximo: use `PPU_WW_GUARD=1` para atribuir escritas da página. Se for DMA,
  capture valor/resultado após MFC executar; não force sinal nem pule o wait.
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

1. Menu original navegável e seleção de modo/time/cena.
2. Cena com jogadores, bola, animação, física e regras originais verificadas.
3. Partida completa, pausa, retorno ao menu, controles e áudio sincronizado.
4. Salvar/retomar progressão, modos offline e matriz de estabilidade/performance.
5. Build e execução reproduzíveis fora da pasta de desenvolvimento.

Só detalhar o marco seguinte quando houver evidência suficiente. Online e melhoria
visual avançada continuam posteriores à base offline funcional.
