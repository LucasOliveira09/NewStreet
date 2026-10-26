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
- 142 testes do projeto, 44 Boot e 65 amostras de assets passaram.

## 1. Traduzir spuroute com entrada relativa d8

- Fonte1ffb680, tamanho1120, base12f00/PC12fd8; SHA no checkpoint.
- PIC modo1; code_start30, entryd8, code_end1110, callback170.
- Mesma init com contexto, mas parametrizar o ponto de entrada do fixture.
- Aceite: tradução sem pendências e init em quatro bases; não alterar cabeçalho
  para forçar entrada30. Preservar imagem, callbacks, contexto e guardas.
- Rodar ensaio nativo estrito e continuar rumo a menu/partida.

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
