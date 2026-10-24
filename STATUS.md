# Estado para retomada

Atualizado em 24/10/2026 durante a integração de boot nativo.

## Implementação comprovada

Baseline técnico no commit `e96e614`: duas funções reais compiladas para Windows,
20.020 retornos inteiros aprovados e 16 testes do runtime aprovados.
As evidências e limites estão em `README.md` e `reports/validation.json`.
O novo executável `private/build/boot/fifa_boot.exe` executa a inicialização real
do EBOOT: TLS, mutexes, módulos, callbacks, consultas de PARAM.SFO e filesystem.
O EBOOT captura `sys_game_process_exitspawn2`, executa seu callback de encerramento
e inicia outro executável Windows com o código recompilado do FIFAZF. O teste
integrado chegou à entrada `0x23770`, com TOC `0x21d5370`, TLS de 684 bytes e
`argc=2` preservado. A cobertura incremental contém 512 funções/trechos do jogo
e 369 stubs de importação. O primeiro alvo ausente nessa cobertura é `0x17841e0`
(LR `0x23b9c`); a execução para com código 90. Não houve frame, menu ou partida.

A geração ampliada contém 98.776 entradas/trechos e compilou/executou em
`private/build/fifazf_full`. Passou pelos 12 alvos observados na cobertura menor.
O serviço `sys_prx_register_library` agora registra os exports reais de
`sys_libc` (560 funções/48 variáveis), `sys_libm` (503/10) e
`sys_libstdcxx` (510/275). A inicialização avançou para criação de threads e
consultas do conteúdo do jogo. O salto computado para `0x43738` foi corrigido
com a descoberta de jump tables do SDK. O jogo avançou até `_cellGcmInitBody`:
context-out `0x22f9370`, command buffer `0x200000`, IO `0x700000` em `0x13f00000`.
O timeout seguinte no controle RSX foi resolvido com consumidor FIFO e relógio
gráfico, iniciados após GCM. D3D12 inicializou na AMD RX 580 2048SP e criou sua
janela de 1280x720. A execução passou a ler `data/loc/locale.big` e iniciou threads
AssetStream::Load/Unpack/Translate. Nenhum flip/frame do jogo foi observado.

O pipeline agora gera código nativo para 14 dos 20 ELF SPU, incluindo a imagem de
5.140 bytes, fingerprint `22F896FE3B85A8C7`, com três segmentos executáveis.
O registro desta imagem usa seu ELF inteiro, sem alias incorreto pelo primeiro
segmento pequeno. A integração é ativada com `-Target Spu` e `-WithSpu` no build.
Isso não comprova que as tarefas funcionam: o runtime foi instrumentado para
parar em programa/salto ausente antes de interpretar instruções ou concluir uma
tarefa sem executá-la. A tentativa estrita em `private/analysis/runs/1792839751667270900`
parou com `spu-indirect`, imagem 526190333, PC/LR `0x3f00c`. O trace mostrou também
grupos distintos iniciando a mesma thread `0x2000`. A causa foi reproduzida e
corrigida: `spu_num` é um número selecionado pelo chamador, separado do ordinal
compacto da thread no grupo. O teste usa três grupos e quatro threads, com números
1, 255, 7 e 2; verifica identidade, argumentos copiados, stores independentes,
status de saída individual e rejeição de requisições inválidas. Antes da correção,
a primeira thread era executada quatro vezes; depois, cada thread executou uma vez.
Logs: `reports/spu-group-before-fix.log` e `reports/spu-group-after-fix.log`.
O novo teste usa os handlers reais do SDK em Windows, sem interpretação de CPU.
Fonte do mapeamento: [RPCS3 aa9ebd2f, sys_spu.cpp](https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/lv2/sys_spu.cpp)
e sua tabela de números em [sys_spu.h](https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/lv2/sys_spu.h).
Há ainda uma referência PPU não emitida em `0x13a796c` (LR `0x139c444`), observada
na tentativa anterior. Nenhuma conclusão correta de tarefa SPU foi validada.
Isso não comprova correção ou cobertura completa:
304 referências diretas permanecem com diagnóstico explícito. Foram identificados
20 ELF SPU embutidos (750.956 bytes), ainda sem execução validada neste jogo.

As quatro fronteiras de chamadas sem suporte foram exercitadas no runtime real
(HLE, syscall, chamada indireta e função não traduzida). Todas param explicitamente.
O patch do SDK está versionado e sua aplicação é idempotente. Baseline reproduzido.
Sete testes adicionais de boot aprovam as fronteiras sem suporte, a leitura de
ponteiros de 32 bits, os argumentos exatos e o transporte para processo filho
nativo com propagação de seu código de saída, o diagnóstico de exceção nativa e
o registro/despacho de exports com TOC e argumentos preservados. Outro teste
compila uma rotina PowerPC sintética para x64: seis entradas do switch aprovadas,
com pilha e r31 preservados. O registro
distingue biblioteca, NID e função/variável; valida antes de publicar a tabela.
O hook HLE de callbacks foi ligado ao dispatcher OPD real. O teste passa oito
argumentos de 64 bits, preserva a identidade da thread e restaura o contexto
do chamador. Callbacks sem função recompilada agora também param explicitamente.
O perfil ampliado usa `/Od` na investigação; `/O1` pode ser ativado para medição
posterior. Seis imagens SPU ainda têm palavras não decodificadas; o inventário
em `private/generated/spu/inventory.json` declara `complete=false`. A geração
parcial é explícita e qualquer imagem requerida sem código deve parar.
Os 12 testes do pipeline SPU passaram, incluindo execução compilada através de
dois segmentos separados. Os sete testes de boot e os 16 CTest passaram após a
política de execução nativa; logs em `reports/spu-pipeline-tests.log`,
`reports/spu-strict-build.log` e `reports/runtime-after-spu-dispatch.log`.
Após a correção dos grupos, passaram oito testes de boot e os 16 CTest
(`reports/runtime-after-spu-group.log`). A nova geração também emitiu `0x13a796c`.
O cache de fontes geradas foi ajustado para UTF-8 explícito, migrando fontes
legadas sem falhar na leitura nem regravar saídas idênticas.

## Primeira tarefa pendente

Validar o mapeamento corrigido no jogo e investigar o próximo salto/serviço
necessário. Rebuild ampliado com SPUs e `0x13a796c` em andamento nesta sessão;
não assumir execução validada apenas porque a função foi emitida.
Janela ou flip, isoladamente, não provam frame correto.
Resolver o próximo bloqueio real de instrução, serviço ou fluxo; manter os logs
em `private/analysis/runs`. A ferramenta encerra a árvore que iniciou no timeout.
Usar os dados reais de `private/disc`; conferir `reports/native-boot-checkpoint.json`.

## Dependências conhecidas

- REA 6.7.0 recusa o ELF PPC64; usar ferramentas de análise compatíveis.
- O runtime ainda precisa ser integrado ao startup e às dependências deste jogo.
- A contagem de nomes importados não comprova serviços implementados.
- ReStreet usa a edição Xbox 360 e permanece referência para online futuro.

Mantenha código autoral, scripts e patches em commits; preserve os dados privados
fora do histórico. Atualize este estado após o próximo incremento validado.
