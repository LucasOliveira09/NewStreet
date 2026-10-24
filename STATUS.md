# Estado para retomada

Atualizado em 24/10/2026 durante a integração de boot nativo.

## Checkpoint atual

A extração foi corrigida para a visão UDF 2.50: o nome original é
`data0.big.sdat`, enquanto ISO9660 o representa como `DATA0_BIG.SDAT`.
A conferência completa leu 104 arquivos, 4.800.945.013 bytes, sem alterar a ISO.
Três testes UDF verificam nomes distintos, bytes reais, mapeamento fragmentado,
limites e alocação esparsa rejeitada; os cinco testes ISO9660 também passaram.
A tentativa `1792846418492465200` abriu DATA0, descriptografou 7.467.087 bytes
com magic BIG4 e iniciou tarefas antes ausentes. O novo bloqueio estrito é
SPU PC `0xb0`, thread `0x2004`: overlay `AssetStream_refpack.elf`, fonte
`0x1e59200`, que ainda precisa ser ligado e validado. A tabela de input vazia
foi observada antes desta correção; sua resolução ainda não foi confirmada.

A implementação já liga 14 ELFs SPU e os overlays zlib/SportsRNA, com validação
de identidade no DMA e invalidação de código sobrescrito. Dezesseis testes de
boot passaram. O FS agora usa os mesmos mounts em Open/Write/Rename, e o runner
mantém HDD0/HDD1 em `private/userdata`. No jogo só foram observados clears pretos:
nenhum frame com desenho, menu, partida, áudio, save ou progressão foi validado.
As saídas dos descompactadores ainda precisam de comparação byte a byte.

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

A geração ampliada inicial continha 98.776 entradas/trechos e compilou/executou em
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
A tentativa `1792840726917801500` confirmou no jogo seis grupos com threads
distintas `0x2000`–`0x2005` e argumentos próprios, sem a falha SPU anterior.
Também passou por `0x13a796c`. O bloqueio atual é PPU `0x138a208`, LR `0x138a1b8`.
Nenhuma conclusão correta de tarefa SPU foi validada.
Isso não comprova correção ou cobertura completa:
Havia 304 referências diretas com diagnóstico explícito. A descoberta foi
corrigida para revisitar ranges quando uma nova fronteira muda o destino de seus
saltos internos. A geração passou a 99.127 entradas/trechos e 369 imports, sem
referências diretas pendentes e sem atingir o limite de seleção. Isso não cobre
automaticamente todo código indireto. Três testes PowerPC sintéticos verificam
a divisão tardia, loops e limite explícito; o primeiro falhava antes da correção.
Os roots observados aceitos estão em `startup_roots.json`, associados ao hash do
ELF, para reprodução sem depender apenas do cache privado.
Foram identificados
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
Outro teste reproduziu seleção incorreta de um programa SPU por endereço de
entrada compartilhado. A política estrita agora exige identidade de conteúdo
antes dessa seleção. Nove testes de boot passaram, incluindo essa regressão
(`reports/spu-image-before-fix.log` e `reports/spu-image-after-fix.log`).
Os testes de terminação SPU também reproduziram continuidade após `stop 0x102`,
parada sem suporte tratada como retorno e salto a LS zero tratado como conclusão.
A política estrita agora interrompe toda a cadeia nativa nos exits suportados,
diagnostica os demais stops e deixa LS zero seguir ao dispatcher real. Uma thread
que retorna sem protocolo de saída também para com `spu-fault`, em vez de status 0.
Onze testes de boot e 16 CTest passaram (`reports/spu-stop-before-fix.log`,
`reports/spu-stop-after-fix.log`, `reports/runtime-after-spu-stop.log`).

## Primeira tarefa pendente

A tentativa `1792841573057646600`, após a correção da descoberta, avançou para
consultas de scripts `data/fifarna/lua/...` e parou em salto SPU: imagem 526190333,
thread `0x2005`, LS PC `0x100`, link `0x3fbb4`. É necessário capturar o local store
e os registradores para identificar código carregado por DMA/overlay e
traduzir seu caminho real. Nenhum flip/frame foi observado.

A captura foi implementada e validada: 256 KB de local store e os 128 registros,
separados por thread/imagem/PC no diretório privado da tentativa. A execução
`1792842082406795800` capturou a tarefa real. Seu bloco de 25.776 bytes em LS
`0x80` coincide byte a byte com o conteúdo original em EA `0x1e59c80`; contém a
etiqueta `AssetStream_zlib.elf`. O código começa em `0x100`; o `bi $r0` em
`0x573c` precede os textos de dados em `0x5740`. A tradução exploratória, ainda
sem integração/execução, produziu 406 entradas, zero instruções desconhecidas e
zero referências diretas pendentes. Registrar e executar esse overlay com
identidade/ownership corretos é a próxima tarefa. Não substituir a descompressão
por retorno de sucesso. Evidências em `reports/spu-overlay-identification.json`.
Após o incremento de captura, passaram 12 testes de boot, os 16 CTest e os 12
testes de geração SPU. Os dumps continuam excluídos do Git.

Os overlays raw agora são reproduzidos por `tools/lift_spu_overlays.py` a partir
de `spu_overlays.json`, sem transformar dados de strings em instruções. A função
extra `0x18c` (zlib) e `0x134` (patch) cobre os saltos calculados da limpeza de BSS.
O jogo chegou a um novo estágio de arquivos/cache. Quatorze testes de boot passaram
após o registro protegido dos overlays; logs em `reports/spu-overlay-ownership-build.log`.
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

### Diagnóstico da tabela de controles

Capturas opcionais de memória PPU foram integradas ao encerramento estrito.
Os dumps ficam em `private/analysis/runs/<id>/ppu`; somente páginas realmente
comprometidas e legíveis são copiadas, com limite de 16 ranges de 4 MiB.
O teste captura bytes OPD conhecidos pelo runtime real; 16 testes de boot passaram.
A tentativa `1792845878958364600` confirmou o manager `0x1070e4b0`, tabela
`0x10cbf3a0`, 137 buckets e zero entradas. A tentativa `1792846051784727600`
identificou requisições de `buttonData.ini` e `buttonDataKeyBoardMouse.ini` antes
da chamada nula. A ISO foi extraída pela visão primária ISO9660, que contém
`DATA0_BIG.SDAT`; o jogo procura `data0.big.sdat`. A relação com o nome UDF
e a leitura/descriptografia do arquivo ainda precisam ser verificadas.
