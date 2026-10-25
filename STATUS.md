# Estado para retomada

Atualizado em 24/10/2026 durante a integração de boot nativo.

## Checkpoint atual

O primeiro frame original foi conferido visualmente: logo FIFA Street sobre
seu fundo, renderizado em D3D12 pelo fluxo nativo do jogo, 1280x720. O manifesto
registra DRAW e textura, não apenas clear. A captura mais antiga já estava na
tentativa `1792846643102912600`; a imagem foi inspecionada somente depois.
As afirmações históricas abaixo de ausência de frame eram conservadoras e
ficaram desatualizadas: a inspeção das capturas confirmou o marco, sem menu.
SHA-256 do BMP: c0082e623bc60e8a4601ce4f3ae2a0c01f32a2b6fe71315538246ecfc5baa84f.

A consulta NP offline e a enumeração de diretórios já foram corrigidas e
validadas. O EOF de Readdir deixava o último tipo de arquivo no buffer e prendia
a thread DLC; o adaptador agora respeita a diferença entre HDD0 e HDD1. Os 21
testes de boot e 37 métodos de teste do projeto passaram após essa correção.

Há 14 ELFs SPU e 17 programas raw compilados, incluindo ANT kernel e generic
player, mais doze posições adicionais (29 registros raw no total). O build
passa, mas o alcance varia entre tentativas concorrentes. A execução mais
recente, 1792873875418408300, foi encerrada aos 75,265 s sem fronteira estrita.
O registro optativo confirmou entradas reais de nove programas da primeira
cadeia (AssetStream, patch, mixer, submix, sample capture, gain, VU e DAC).
ANT e generic player ainda não tiveram suas entradas confirmadas nessa coleta.

O watchdog mostra main em sleep, mutex 8 com dono thread 22 e outra thread
esperando esse mutex. Próximo passo: examinar a stack do dono e as consultas
NetCtl offline restantes, sem forçar flags/callbacks. Logo original validado;
menu, som audível e partida pendentes. 24 testes de boot e 40 do projeto passam.

`tools/identify_spu_resident.py` produz evidências limitadas a partir do snapshot
e dos segmentos PT_LOAD do ELF com hash fixado. Não admite programas nem altera
configuração automaticamente. Cabeçalhos, tamanho e limites de código exigem
revisão porque os módulos contêm dados e usam layouts diferentes.

Os 16 CTest do runtime passaram. A extração UDF verificou 104 arquivos,
4.800.945.013 bytes, preservando DATA0. As 47 capturas AssetStream observadas
(15 RefPack, 32 DEFLATE, 2.671.706 bytes de saída) coincidiram integralmente
com oráculos independentes, sem capturas incompletas; limite de 32 por codec.
Áudio audível, menu, partida, saves e progressão continuam sem validação.

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

### Overlay RefPack

Fonte original `0x1e59200`, tamanho `0xa80`, LS base `0x80`, entrada `0xb0`.
A fronteira executável termina em `0xa70`, depois do retorno em `0xa6c`;
a região seguinte contém máscaras e o nome `AssetStream_refpack.elf`.
O LS capturado difere apenas em dados posteriores ao código: o intervalo
executável coincide byte a byte com a fonte. A tradução tem 42 funções,
zero instruções recusadas e zero alvos diretos pendentes. O resultado de
descompactação ainda não foi validado contra um oráculo independente.

### Mixer de áudio SPU

`spumixer.elf` em `0x2006280`, 0x3300 bytes, foi traduzido e ligado.
A entrada é LS `0xb0`, com código até `0x31d8` e BSS até `0x3730`.
O salto calculado da limpeza de BSS foi observado em `0x148` e incluído
como fronteira traduzida; os callbacks publicados pelo próprio código em
`0x2cb8` também foram identificados. Não houve opcode recusado ou alvo
direto pendente. A tentativa `1792846844059816000` executou a inicialização
do mixer até a chamada de seu módulo PIC `spusubmix.elf`, copiado integralmente
para LS `0x3780`, entrada `0x37b0`, fonte `0x1fb3580`. A parada estrita
nesse ponto preserva o estado. Áudio audível e correto ainda não foi validado.

### Submix PIC e build incremental

O módulo `spusubmix.elf` foi traduzido para a base LS observada `0x3780`,
com hash da fonte e callbacks PIC `0x3848`/`0x38c0` verificados. A tentativa
`1792847030174348200` passou por sua inicialização e alcançou o próximo
módulo do mixer, `spusamplecapture.elf`, carregado em LS `0x4880`, entrada
`0x48b0`, fonte `0x1ffc800`; todos os bytes capturados coincidem com a fonte.
Essa tradução ainda usa a base observada; outra posição precisa ser admitida
explicitamente. Não há relocação dinâmica/JIT de CPU.
O gerador agora preserva mtime apenas para arquivos regenerados idênticos
byte a byte, mantendo a publicação completa e a remoção de saídas antigas.
O rebuild do callback compilou somente submix e a tabela HLE, sem recompilar
zlib, RefPack ou o mixer inalterados. Nenhum áudio foi validado.

### Captura de amostras do mixer

`spusamplecapture.elf`, fonte `0x1ffc800`, 0x2260 bytes, foi traduzido
para LS `0x4880`, com código até `0x68e0` e callbacks PIC identificados.
O módulo executou até o mixer carregar `spugainfader.elf` em LS `0x6b80`,
entrada `0x6bb0`, fonte `0x1fda900`. A tentativa é `1792847260676890600`.
O dump dessa nova região coincide integralmente com a fonte original.
Nenhuma amostra de áudio audível foi validada.

### Oráculos dos dados AssetStream

O observador opcional registra input antes e output depois do retorno real,
incluindo tail transfers nativos. O teste Windows compara execução observada
e sem observação, com e sem frame host já ativo, conferindo GPR de retorno,
PC, profundidade, pendência e bytes produzidos após o tail. Os 17 testes de
boot passaram. O decoder diagnóstico RefPack cobre as cinco classes de comando,
lookbacks sobrepostos, headers de 24/32 bits, tamanho comprimido opcional,
limites e entradas truncadas (três testes adicionais aprovados).
`--observe-assets` isola dados por tentativa e acusa inputs sem retorno capturado.
Os 47 jobs comparados passaram integralmente; relatório autoral em
`reports/asset-job-validation.json`, dados privados na tentativa acima.
O host não usa o oráculo para executar ou substituir os descompactadores SPU.

### Mais de quatro módulos residentes

Um teste Windows dos handlers reais carregou sete módulos em spans LS
independentes. Antes da correção, o runtime recusava silenciosamente a
identidade do quinto ao sétimo e parava em `spu-indirect`. A capacidade foi
alinhada ao limite de 128 fontes registradas, e todos os loops percorrem
o tamanho real da tabela. Esgotar a capacidade agora produz diagnóstico
estrito `spu-overlay-capacity`. O teste mantém e despacha os sete módulos;
os 18 testes de boot passaram. O patch do SDK inclui também a mudança de
layout de `spu_context`, exigindo rebuild de runtime e traduções SPU.

### Ganho e volume do mixer

O módulo `spugainfader.elf` foi ligado com base LS `0x6b80`, entrada
`0x6bb0`, fonte `0x1fda900`, 0x27c0 bytes e código até `0x9320`.
O callback PIC `0x6c38` e os sete valores da jump table em `0x8d6c`
foram conferidos no binário; seus cinco destinos distintos foram incluídos
como fronteiras. A tradução tem 157 funções, zero instruções recusadas e
zero alvos diretos pendentes. A execução `1792869024593523500`, já com
a nova capacidade de módulos residentes e todos os artefatos recompilados,
passou pelo ganho/volume até o módulo VU em LS `0x9430`, fonte `0x2004e00`.
Os 18 testes de boot e os 16 CTest do runtime passaram. O rebuild sequencial
completou; a tentativa sobreposta não foi usada como evidência. O link local
foi limitado a quatro threads no cache CMake, sem alterar código de produção.

### Medidor VU

`spuvumeter.elf`, fonte `0x2004e00`, 0x12e0 bytes, está ligado em LS
`0x9400`, entrada `0x9430`, código até `0xa6e0`. O callback PIC em
`0xa160` e os cinco destinos distintos da tabela em `0xa624` foram
conferidos no original. A tradução tem 54 funções, sem instruções recusadas
ou alvos diretos pendentes. A tentativa `1792869100339436500` passou pelo
VU e alcançou o DAC SPU, fonte `0x1fb4600`, carregado em LS `0xa780`,
entrada `0xa860`. O cabeçalho desse módulo tem entrada offset 0xe0,
diferente dos anteriores; não presumir offset 0x30 ou tamanho pelo nome.
A tentativa também repetiu as 47 comparações de assets sem diferenças
e sem capturas incompletas. Ainda não há áudio audível validado.

### DAC SPU

`spudac.elf`, fonte `0x1fb4600`, foi conferido integralmente em 0x2690
bytes no LS e traduzido para a base observada `0xa780`. A entrada fica
em `0xa860`, mas existe uma função real anterior em `0xa7b0`, chamada
diretamente; o verificador recusou a primeira fronteira que a excluía.
A fronteira correta começa nessa função e termina em `0xcbd8`, após o
retorno em `0xcbd4` e antes das constantes. A tradução tem 117 funções,
sem instruções recusadas ou alvos diretos pendentes. O callback PIC `0xb098`
foi identificado no original. O boot passou pelo DAC até o import NP acima.
O gerador agora detalha seus motivos de rejeição (opcode, alvo direto ou entrada),
sem publicar uma geração incompleta. Nenhum áudio foi validado.

### Região NP offline e observação de esperas

NID 0xb1e0718b identificado pelo algoritmo de NID e pela assinatura em
RPCS3 aa9ebd2f, sceNp.cpp. O adaptador usa a inicialização e o modo NP reais
do runtime; retorna os erros correspondentes e preserva os out params.
No modo online não suportado, encerra com diagnóstico próprio. Dois testes
Windows exercitam NID/dispatch, inicializar/terminar, ambos os ponteiros nulos,
bytes sentinela e a fronteira online, sem conexão de rede.
`FIFA_WATCHDOG_AFTER_MS=25000` coleta uma amostra de LR/GPR/serviços das
threads, apenas no FIFAZF, sem suspender nem modificar seu estado. São dados
de melhor esforço: LR isolado não distingue progresso de loop. O runner agora
inclui hashes e metadados das capturas D3D12 para não perder evidências de desenho.

### Fim de diretório no HDD0/HDD1

A amostra anterior mantinha DLC em cellFsReaddir. O código original em
0x12d0dc testa d_type para terminar a leitura, sem usar nread. O runtime
zerava apenas nread, deixando a última entrada ativa para sempre.
RPCS3 aa9ebd2f, sys_fs.cpp, confirma que HDD0 e outros mounts escrevem
d_type=0, d_namlen=0 e d_name[0]=0 no EOF, preservando o restante do último
registro; HDD1 repete o último registro integral. Ambos escrevem nread=0
depois da estrutura. O adaptador passou a manter essa distinção e rejeitar
ponteiros nulos/fora da VM e descritores inválidos. Não altera flags do jogo.

Quatro cenários Windows reais (HDD0/HDD1, vazio/preenchido) falharam antes
e passaram depois, inclusive com o buffer envenenado entre chamadas e EOF
repetido, tamanho big-endian e bytes da última entrada preservados. São
21 testes de boot e 37 testes do projeto aprovados. A tentativa
1792870440169761500 mostrou a thread DLC em sleep de 1 segundo (LR 0x12e910),
saindo da leitura infinita; o main estava em carregamento de recursos aos
10 segundos (LR 0x123c3a8), com a cadeia salva na pilha guest capturada.
O processo chegou ao timeout de 25 segundos sem novo erro estrito.
Há uma observação mais longa em andamento; menu ainda não foi validado.

O cache DATA4.BIG foi conferido: 30.585.168 bytes, SHA-256
4b32a59c753d11c77e67cfbe9ac4e0374b97039717a744bb1f8a897884f2c53b,
igual ao arquivo original do disco. A hipótese de cache truncado foi descartada.

## Reamostragem de áudio nativa

O plugin `audio_spuresample` foi identificado por cabeçalho e 4.080 bytes
iguais ao original: fonte 0x1fc6f00, SHA-256 783135b9116bf79bc0ccdde85755b8acf4fa58650dd3da20eee3147f70d9680b.
A inicialização PIC calcula callbacks 0x39c0/0x3b68. A tabela relativa em
0x4754 tem cinco destinos distintos conferidos; todos foram incluídos.
A geração contém 41 entradas, zero instruções ou destinos diretos ausentes.
Build Windows aprovado; tentativa 1792870968800232800: os 47 jobs AssetStream
continuam iguais aos oráculos, a captura tem o mesmo logo, e a parada estrita
avançou para o próximo plugin, rechannel em LS 0x49b8, após 30,266 s.
Próximo passo: recompilar o módulo observado sem substituir processamento.

## Sobreposição de módulos SPU e rechannel

O plugin rechannel (fonte 0x1fc6000, 3.664 bytes, SHA-256
2d067497ef05949454811eda45594b786459d3f4e2ff1c5fc6139454fd0cb48f)
foi recompilado em 56 entradas, com callbacks 0x49b0/0x4a48 e código até
0x56d8, incluindo os tail branches após o último retorno. A primeira execução
repetiu a parada em 0x49b8 apesar de todos os bytes coincidirem.

Causa: o tombstone de sample capture cobria uma região maior que o novo módulo
e era escolhido antes dele. O runtime agora mantém intervalos de instruções
disjuntos: divide os trechos atingidos por DMA, preserva código externo, ajusta
a origem de cada trecho e substitui somente a região do módulo novo. Código
desconhecido continua recusado; recarregar o módulo maior retoma sua identidade.
Uma regressão Windows com imagem aninhada falhou antes e passou depois; inclui
DMA em chunks e sobrescrita desconhecida de uma entrada traduzida.

22 testes de boot e 16 CTest do runtime aprovados. Build completo aprovado.
Tentativa 1792871321610938400 passou por 0x49b8 e parou em outro módulo,
PC 0x5970, após 33,070 s; as 47 saídas de assets continuam iguais aos oráculos.
O logo conserva o mesmo hash. Não comprova menu, áudio audível ou gameplay.

## Packet player nativo

Fonte 0x1febb00, LS 0x5880, 3.888 bytes iguais ao original, hash
4caa8a2f7d6d4771783f9f72b6b0a5bcf50357651672cd6113c68ff5f0cff888.
A inicialização PIC usa callbacks 0x58e0, 0x58b0 e 0x5d58, todos revisados.
Geração com 35 entradas, sem instruções ou destinos diretos ausentes; build
aprovado e boot avançou de 0x5970 para 0x6a10 no próximo programa residente.
Evidência: tentativa 1792871415455714000; logo com o mesmo SHA-256.

## Inicialização do decoder e segunda posição PIC

`audio_spudecoder`: fonte 0x1f8f880, LS 0x6880, tamanho 3.648, hash
2f734f872a4578670362e43683e8e2df2e30ccc0b61ba63aaec1bd070075279a.
Os callbacks PIC 0x68b0/0x69a8/0x6968/0x6c08 foram conferidos, com código
até 0x75ac. Geração de 38 entradas sem instruções/destinos diretos ausentes.
Build aprovado; tentativa 1792871490342211600 passou por sua inicialização e
parou no loader ao carregar o submix original em uma nova base LS, 0x7800.
A fonte e o cabeçalho correspondem a 0x1fb3580, já traduzido em LS 0x3780;
a base inesperada é corretamente recusada. Próximo incremento: admitir essa
posição observada, recompilar estaticamente e testar a seleção por base.
O identificador agora examina toda a LS: uma falha de DMA ocorre antes do salto
e o novo módulo pode estar acima do PC do loader. Não há JIT/interpretação.

## Segunda base estática de submix

`additional_ls_bases` admite posições adicionais conferidas. O gerador desloca
as entradas/limites e recompila o mesmo blob original para cada posição, com
símbolos e registro de imagem distintos. Hash e verificação de origem continuam
obrigatórios. O runtime procura a variante da origem/base efetivamente pedida;
se nenhuma existir, preserva o diagnóstico `spu-overlay-base`.
A regressão Windows da segunda base falhou antes e passou depois. 23 testes de
boot, 39 do projeto e 16 CTest aprovados. Build e execução reais alcançaram
sample capture em LS 0x8900 (fonte 0x1ffc800, todos os 8.800 bytes iguais).
A nova posição é o próximo incremento, sem afrouxar a seleção por identidade.

## Sample capture na segunda cadeia de áudio

A segunda posição, LS 0x8900, foi conferida no snapshot e compilada
estaticamente a partir do mesmo blob. Geração/build aprovados; tentativa
1792871762724335900 avançou para outra carga de módulo em LS 0xac00,
recusada por base ainda não admitida. O logo mantém o hash anterior.

A posição adicional de gain fader em LS 0xac00 foi conferida integralmente,
compilada e alcançada. Tentativa 1792871837562167900: próxima recusa de base
em 0xd480, após 30,225 s. Geração sem instruções/destinos diretos ausentes.

A segunda posição de VU meter, LS 0xd480, também foi conferida e compilada.
Tentativa 1792871899123215200: 90,238 s até o timeout controlado, sem nova
fronteira estrita. O jogo ainda apresenta o logo; chamadas repetidas de NetCtl
são observadas, sem atribuir a elas a causa da espera antes da amostragem.
Próximo passo: watchdog, profiler e capturas posteriores para localizar o fluxo.

## Estado NetCtl offline

O SDK retornava NOT_INITIALIZED após Init ao consultar uma conexão offline,
um desvio específico de outro título. A referência fixada distingue o ciclo
de vida da biblioteca do estado Disconnected. GetState agora retorna a consulta
bem-sucedida com estado zero nessa configuração, preservando erros antes de
Init/depois de Term e endereço nulo. Não declara conexão/IP obtido.
Regressão pelos handlers HLE reais falhou antes e passou depois, conferindo
retornos, escrita big-endian e buffers preservados nos erros; 24 testes de boot
aprovados. Build completo/teste integrado em andamento, sem concluir que isso
resolva a espera no mutex. Fonte: RPCS3 aa9ebd2f, cellNetCtl.cpp linhas 125–142.
https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/Modules/cellNetCtl.cpp#L125

## DAC na segunda cadeia e próximo sound player

O DAC original foi conferido integralmente em LS 0xe800, fonte 0x1fb4600,
SHA-256 5a756bdec8d54872b5f8084554796b34168d7ed2b56e8a432ab57a682b37f8f5.
A variante estática compila e sua entrada passa no boot. Tentativa
1792872486371238400: próxima parada estrita em 0x5a88, após 31,714 s,
`spusndplayer1.elf`, fonte 0x1fca800, LS 0x5880, 7.648 bytes iguais.
Os frames 1, 101 e 201 ainda mostram um draw de abertura; menu não aceito.
O watchdog optativo também informa donos/depth dos mutexes ativos, sem
suspender threads, adquirir seus locks ou alterar o guest. A nova coleta
ainda não foi necessária nesta tentativa, que para antes dos 45 segundos.
24 testes de boot e 40 do projeto passaram após as mudanças.

## Sound player 1

`spusndplayer1.elf`: fonte 0x1fca800, LS 0x5880, 7.648 bytes iguais,
hash a02440fa022f36c82fabb5fc967c18425ae77dbd3cf76fa3e876a408a28ae3bf.
Callbacks 0x59e0/0x59b0/0x5ff8 revisados na inicialização PIC; código até
0x7634, incluindo os tail branches finais. 87 entradas, zero instruções
ou destinos diretos ausentes, build aprovado. Tentativa 1792872592369669300
passou por sua entrada e pediu o decoder em outra posição: LS 0x7700.
O novo snapshot confere os 3.648 bytes do mesmo decoder original.

A posição do decoder em LS 0x7700 foi recompilada a partir dos mesmos bytes
e passou pela inicialização. Tentativa 1792872755839411100: próxima carga
em LS 0x8680 é packet player, não submix. O descriptor real em LS 0x2d9e4
contém fonte 0x1febb00 e tamanho 0xf70, incluindo a etiqueta BuiltElfName.
A ordem depende do encadeamento do mixer; não presumir uma lista fixa de
módulos ou admitir posições somente por uma soma de tamanhos.

Packet player foi recompilado em LS 0x8680 e sua entrada passou no boot.
Tentativa 1792872903594774400: próxima carga em LS 0x9680, após 26,103 s.
O dispatcher mantém a seleção por origem/conteúdo/base, sem interpretação.

## Outras posições observadas do mixer

Cada posição foi admitida somente depois de um snapshot com o programa
inteiro igual à origem e a um programa já conhecido com variantes PIC testadas.
O gerador recompilou suas entradas e limites para a base física, com zero
instruções/destinos diretos ausentes. Build e boot foram repetidos em sequência.

| Programa/base | Tentativa após integrar | Próxima base estrita |
| --- | --- | --- |
| submix 0x9680 | 1792873107009892400 | 0xa780 |
| sample capture 0xa780 | 1792873163895030300 | 0xca80 |
| gain fader 0xca80 | 1792873225651043600 | 0xf300 |
| VU meter 0xf300 | 1792873318036992900 | 0x10680 |

A primeira preparação do quarto build falhou antes de compilar porque o
ambiente VS, reinicializado repetidamente na mesma sessão PowerShell, estourou
o limite de linha do cmd. A execução em processo limpo compilou e validou
o quarto incremento. A correção de reuso do ambiente é uma etapa separada.

## Reuso do ambiente de build

A reinicialização do DevShell na mesma sessão fazia PATH crescer de 4.712 para
6.144 e 7.576 caracteres; a quarta chamada falhou com "linha de entrada muito
longa". O build agora reutiliza o ambiente se instalação e arquitetura host/
target x64 já coincidem, e não duplica os diretórios LLVM/Ninja no PATH.
Quatro builds Probe completos consecutivos passaram na mesma sessão, com PATH
estável em 4.719 caracteres e Git encontrado nas quatro chamadas. Cada Probe
exercitou os 20.020 retornos inteiros; isso valida o build repetido, sem ampliar
a alegação de conformidade da CPU. Logs privados repeated-build-1..4.log.

## Terceiro DAC e chegada ao ANT kernel

A posição LS 0x10680 do DAC foi conferida e recompilada. A tentativa
1792873477390004500 avançou para outra thread SPU, 0x2005 (Rendering),
PC 0xb0/LR 0x3fbb4. O residente corresponde ao `ANT_kernel.elf`, cuja
tradução anterior foi recusada por 18 palavras não reconhecidas em dados.
A etiqueta seguinte não delimita esse blob; o cabeçalho e seu ELF embutido
identificam o segmento LS 0x80..0x122a0 (74.272 bytes), todos iguais ao original.
SHA-256 do segmento: d68cd459a32c7a136cace588821fbe18accefdd488ae79a2b7961d5f50576ed0.
O código termina em 0x109e8; há tabelas/constantes depois. Próximo passo:
recompilar o intervalo real, preservando dados e BSS e a parada estrita.
Nesta tentativa, 64 saídas AssetStream capturadas passaram (limite 32 por
codec, não exaustivo). O mix de 1.710.592 floats ainda é inteiramente zero.

## Tradução limitada do ANT kernel

O intervalo real 0xb0..0x109e8 gerou 803 entradas, sem instruções/destinos
diretos ausentes. Os dados 0x109f0..0x122a0 continuam intactos, fora do código
traduzido, e a entrada 0x154 da limpeza de BSS foi incluída. Build aprovado.
A execução 1792873669502836500 parou primeiro na thread de áudio, em outro
programa (`spugenericplayer`, entrada 0x59e0). A ausência do erro anterior
não comprova conclusão do ANT: adicionar registro optativo de entradas nativas
para distinguir carga, início de execução e conclusão de tarefa. Nesta execução
49 saídas AssetStream coincidiram com as referências; em 1792873477390004500
foram 64. A quantidade varia com o primeiro bloqueio concorrente.

## Generic player e evidência de entradas

O generic player (fonte 0x1fdd100, LS 0x5880, 7.088 bytes) foi conferido
inteiro. SHA-256 ffee4cb8e3baabeaa85751f34483b3b835ef7f2143681a063fcafb94cb5614a3.
Callbacks 0x5ad0/0x59b0/0x6070, código até 0x7404. Geração de 82 entradas,
zero instruções/destinos diretos ausentes; compilação aprovada.
`FIFA_SPU_ENTRY_TRACE=1` registra uma vez por programa/base a entrada real,
antes de delegar ao código original. Registro usa atomic_flag, limite 128,
e não escreve estado guest; o observador de assets mantém seu comportamento.
O runner preserva essas entradas no result.json. A execução de 75 s registrou
nove programas da primeira cadeia, sem comprovar entrada/conclusão do ANT ou
do generic player. As 47 saídas AssetStream capturadas continuaram corretas.
40 testes do projeto passaram.

## Consulta de IP no modo offline

O handler cellNetCtlGetInfo(16) devolvia sucesso/IP mesmo desconectado.
Agora retorna NOT_CONNECTED, preservando o buffer, e mantém INVALID_ADDR
para ponteiro nulo. A regressão pelos handlers reais falhou antes e passou
depois; 24 testes de boot e build completo aprovados. Não altera o caminho
online. Referência fixada: RPCS3 aa9ebd2f, cellNetCtl.cpp, GetInfo.
https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/Modules/cellNetCtl.cpp#L224
A execução 1792874176576705900 registrou 28 entradas reais de programas/bases
SPU, incluindo ANT em 0xb0. Parou em seu salto calculado para 0x11c, após
34,481 s. Isso confirma entrada no ANT, sem comprovar conclusão, áudio ou menu.
O frame capturado continua sendo o logo original.

## Caminhos com barras iniciais repetidas

O jogo abre //dev_hdd1/replay0.bin e //dev_hdd1/audioreplaydata.dat.
Os adaptadores não reconheciam o mount e apontavam para o disco. Context HLE,
generic cellFs e sys_fs agora reduzem somente as barras iniciais repetidas
antes de selecionar o mount, preservando os diretórios configurados.
A regressão Windows falhou nos dois cenários repetidos antes da correção;
os quatro cenários (padrão/override, normal/repetido) e os 24 testes de boot
passaram depois. O ciclo testa criação/escrita/rename/leitura pelos handlers
reais e concordância do tradutor syscall; integração no jogo ainda pendente.
Referência de parsing VFS: RPCS3 aa9ebd2f, VFS.cpp.
https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/VFS.cpp#L219

## Entrada calculada do ANT e acompanhamento ao vivo

A limpeza da BSS calcula 0x154 - ((0x3b180-0x122a0)&255)/4 = 0x11c.
O destino contém os stores originais do bloco parcial, conferidos no snapshot
1792874176576705900; foi incluído na tradução estática (804 entradas, zero
instruções/destinos diretos ausentes), com build completo aprovado. Não há
conclusão do ANT validada: as tentativas seguintes aguardaram trabalho da
renderização ou pararam antes na thread de áudio. A tentativa com SPU_PCSAMPLE=5
1792877484736736600 confirmou entrada real do generic player, depois exigiu
o mesmo decoder em LS 0x7500 (ainda não admitido neste incremento).
O runner grava stdout/stderr direto em arquivos privados, legíveis durante
a execução. Leitura ao vivo e coleta final de parada estrita foram conferidas
nessa tentativa; a política de timeout continua limitada à árvore iniciada.
40 testes do projeto aprovados após a correção de caminhos.

## Captura optativa de SPUs durante uma espera

SPU_PCSAMPLE já existia e foi reutilizado. SPU_PCSAMPLE_DUMP_AFTER=1..300
segundos chama uma vez o observador de diagnóstico em cada contexto com MFC
vivo. O lock compartilhado do registro impede destruição durante a coleta;
a execução não é suspensa, portanto LS/registradores são best-effort.
Arquivos sample-spu-* ficam separados dos snapshots de falha. Sem as variáveis
a coleta permanece desativada. Na execução 1792877940393047300, seis pares
JSON/LS de 262.144 bytes foram registrados uma única vez, sem falha estrita.
Timeout de 65 s encerrou a árvore iniciada; 24 testes de boot aprovados.
A pilha de RenderThread em 45 s passa por 0x18d668/0x18d090/0x18e0c4,
espera por espaço em buffer circular. Investigar os ponteiros/control registers
que esse objeto lê; a captura gráfica continua na abertura, sem menu aceito.
O frame do watchdog e os samples SPU ocorrem em momentos diferentes.

## Posições adicionais conferidas do áudio

Decoder em LS 0x7500 (snapshot 1792877484736736600) e resample em LS
0x3780 (1792877825163692200) conferem integralmente com as fontes já fixadas
em spu_overlays.json. Ambas posições foram recompiladas estaticamente, com
zero instruções/destinos diretos ausentes, e build completo aprovado. Não houve
entrada registrada nessas variantes nas últimas tentativas, que aguardaram
na inicialização antes delas. Não confundir posição admitida com tarefa concluída.
A tentativa 1792877825163692200 também registrou a entrada real do ANT.

## FIFO gráfico sem descarte de comandos

A execução 1792878491512590600 registrou resync jump-park de GET 0x41750
para PUT 0x621b0: o runtime abandona um self-JUMP após 50 ms. A memória
mostra escritas de label 0x400 com 0x2b22/0x2b23 antes de PUT, enquanto o
label permanece 0x2b1f e RenderThread espera os tokens 0x2b20..0x2b22.
O resync preservava referências, mas descartava comandos necessários.
O host FIFA agora instala cellGcm_fifo_set_fault_handler antes de iniciar
o consumidor. Parks e acquires aguardam o produtor real, sem timeout/bypass;
recuperações que descartariam comandos e palavras desconhecidas param com
GET/PUT. A reciclagem automática que reescreve o contexto do título fica
desativada nesse perfil. O modo legado permanece quando o handler é NULL.
A regressão do walker real falhou antes (park perdeu label, acquire ignorado)
e passou depois, incluindo atualização real do produtor e recusa de JUMP
não mapeado/palavra desconhecida. 26 testes de boot e 42 do projeto passaram.
O boot 1792878833460109400 não fez resync e avançou até outro packet player,
LS 0x5700, em 22,991 s. ANT e rechannel LS 0x4800 tiveram entradas reais.
64 saídas AssetStream coincidem; sem conclusão de ANT/menu/gameplay aceita.
As capturas tardias ainda mostram a abertura, mesmo havendo outros draws.
Após a mudança do FIFO, os 16 testes CTest do runtime também passaram.

## Rechannel e sound player em outras posições

Rechannel em LS 0x4800 e sound player 1 em LS 0x8480 conferem com as
fontes originais fixadas. As variantes compilaram sem instruções/destinos
diretos ausentes. As entradas foram registradas nas tentativas
1792878833460109400 e 1792878491512590600, respectivamente. O decoder
LS 0x7500 também entrou em 1792878293511258800. Start foi consumido pelo
backend nessa tentativa; não demonstra navegação. A captura de áudio contém
3.410.944 floats finitos, todos zero. O próximo candidato confirmado é
packet player em LS 0x5700, ainda não ligado neste incremento.

## API de política FIFO restrita ao host

O gerador de NIDs identifica definições cujo nome começa por cell/sys/sce.
A configuração do callback foi renomeada para
ps3recomp_gcm_fifo_set_fault_handler, evitando registro guest indevido de um
ponteiro de função host. A regressão da tabela real falhou antes e passou
depois. 27 testes de boot e os dois builds passaram; a tabela voltou a 1.201
handlers. Os exports originais permanecem cobertos pela geração existente.

## Captura interrompida não invalida o diagnóstico do boot

A parada SPU da tentativa 1792879100554817400 interrompeu a gravação de
refpack-15.json e o leitor lançou JSONDecodeError antes de salvar result.json.
O validador agora registra metadados ausentes/incompletos como erro e mantém
as outras comparações. A regressão cobre arquivo vazio, JSON truncado, lista
e campos faltantes; os quatro cenários falharam antes e passaram depois.
Reanálise real: 48 registros, 47 saídas iguais, refpack-15 incompleto,
all_passed=false. Isso não demonstra erro de descompressão do jogo nem
aprova a captura interrompida. 44 testes do projeto passaram.
O primeiro bloqueio continua documentado no stderr original, em LS 0xa300;
não há result.json recuperado com duração/exit code inventados.

## Packet player em LS 0x5700 e 0xa300

As duas posições foram verificadas byte a byte contra a fonte 0x1febb00 e
recompiladas com os limites/entradas PIC já auditados, sem instruções ou
destinos diretos ausentes. Build completo aprovado. A execução
1792879324358744800 registrou entrada real em LS 0x5700 e parou na carga
do decoder em LS 0x6700, após 24,816 s. A posição 0xa300 está ligada, mas
ainda não teve entrada registrada. 64 saídas AssetStream passaram. O perfil
FIFO continua sem resync de comandos; menu e áudio continuam pendentes.

## Decoder em LS 0x6700

O decoder foi conferido integralmente nessa posição e recompilado. Build
aprovado; entrada registrada em 1792879595172586800. A parada seguinte,
após 25,646 s, é o pause em LS 0x7680, fonte 0x1ff3480 (208 bytes iguais),
e não se pode deduzir o módulo seguinte apenas pela ordem de outra cadeia.
A próxima etapa mantém a identificação por conteúdo antes de compilar.

## Pause em LS 0x7680 e limite da enumeração de posições

Pause foi conferido, compilado e entrou em 1792879747630265800. A próxima
carga, LS 0x7800, contém sound player 1, não submix. São os mesmos bytes da
fonte 0x1fca800, hash a02440fa022f36c82fabb5fc967c18425ae77dbd3cf76fa3e876a408a28ae3bf.
A tentativa parou após 25,589 s; menu/áudio continuam pendentes. Enumerar
mais combinações de posições do mixer não escala para todo o conteúdo offline.
Próxima etapa: suporte AOT relocável para os programas PIC já admitidos,
com escopo, critérios e verificações em tasks/spu-relocatable-pic.md.

## Runtime para regiões PIC canônicas

Adicionado registro optativo para programas PIC já traduzidos, com validação
de origem/fingerprint, flag PIC, alinhamento e limites físicos. Cada intervalo
residente guarda physical-minus-canonical; recortes preservam o deslocamento.
O dispatcher e a retomada pelo drain consultam ownership antes da imagem base,
incluindo tombstones. A consulta de deslocamento é somente leitura.
A fixture Windows exercita o mesmo programa em três posições simultâneas,
incluindo deslocamento negativo, alteração de dados, recorte de instruções e
recusa de fonte alterada/layout absoluto/base desalinhada/estouro de LS.
Cinco cenários falharam antes da implementação; depois os 29 testes de boot,
46 do projeto e 16 CTest do runtime passaram. Modo ainda não habilitado no jogo: falta
validar a emissão de instruções relativas e integrar o gerador.

## Emissão PIC compilada e fixture nativa

O lifter agora tem modo optativo que desloca PC, links e LQR/STQR por uma
constante local a cada função, preservando operandos absolutos e registradores.
BRA/BRASL são recusados neste modo inicial. Dois programas SPU autorais foram
traduzidos e compilados para x64: oito execuções em quatro bases, incluindo
deslocamento negativo, branches, fallthrough, links e callback entre programas,
passaram. A fixture falhava em base diferente da canônica antes da correção.
Os 30 testes de boot passaram e o build completo com a opção desligada passou.
As 37 fontes SPU anteriores permaneceram byte a byte iguais após regeneração.
A execução 1792881874546096800 parou estritamente após 21,825 s, em outra
posição ainda não admitida, LS 0xb300. Isso confirma que a ordem do mixer varia;
não constitui avanço ao menu nem validação de áudio.

## Integração optativa PIC no gerador

relocatable_pic=true gera uma única imagem canônica e mantém as posições
estáticas históricas no manifesto. O gerador verifica cabeçalho PIC suportado,
entrada relativa, hashes e limites antes de publicar o código AOT. Os wrappers
de entrada registram a primeira base física observada por programa. Três testes
de manifesto passaram; os 51 testes do projeto passaram. Com a flag desligada,
39 arquivos regenerados (37 fontes, registro e lista CMake) ficaram idênticos.
Nenhum programa do jogo foi habilitado neste incremento.

## Diagnóstico das bases físicas de entrada

O observador agora registra a primeira entrada de cada par programa/base,
inclusive várias posições da mesma imagem PIC. O bitmap é limitado à LS,
atômico e não altera o contexto guest. A regressão reproduziu a perda das
segundas posições antes da correção e passou depois. 31 testes de boot,
52 do projeto e os builds de boot/jogo passaram. A mudança é diagnóstico;
uma entrada registrada não demonstra conclusão da tarefa.

## Primeira entrada PIC relocada no jogo

Somente sound player 1 foi habilitado. A execução 1792882100622595900 entrou
em LS 0x5880 e 0x7800 usando a mesma tradução canônica. Não existe variante
estática 0x7800. Após 25,227 s, a falha estrita foi em PC 0x7b60: o conteúdo
nesse endereço já pertencia a outro programa, spudecpcmfloatnative. O snapshot
em base 0x7680 coincide integralmente com a fonte 0x1fa3a00, 0xb80 bytes,
SHA f1d9790891394b24161e8998aeeda641a7b00281bde75daf0ed5d0511937aec0.
As 64 saídas AssetStream capturadas passaram. Entrada do sound player foi
validada; conclusão, áudio audível e menu continuam pendentes. Próxima etapa:
traduzir o decoder PCM float original e ampliar o PIC aos módulos já auditados.

## Cadeias de áudio com AOT PIC e decoder PCM float

Integrado spudecpcmfloatnative, com código 0x76b0..0x81d0, entrada 0x7b60
e callback 0x76b0, conferidos no original. Treze módulos usam agora uma tradução
PIC cada; mixer residente conserva o layout fixo distinto em 0x80. O gerador
recusou esse layout ao selecioná-lo indevidamente; a seleção foi corrigida sem
afrouxar a validação. Os 18 registros resultantes não têm instruções nem
destinos diretos ausentes. Build completo aprovado.
Em 1792882263069156500, houve entradas reais em novas bases, inclusive submix
0xb300, e no decoder PCM float 0x7680. Após 20,862 s, a próxima falta é spusend,
fonte 0x1fc4b80, base 0xac00, entrada 0xac30, 0x1400 bytes iguais ao original.
64 saídas AssetStream passaram. O frame 801 segue com o mesmo logo (42 draws);
1.519.616 amostras de áudio capturadas são finitas e zero. Menu e som continuam
pendentes, sem concluir a execução dos módulos apenas por observar entrada.

## Send, tabela de saltos e primeira saída de áudio com sinal

Integrado spusend (fonte 0x1fc4b80, SHA f8b2a0697a67247e6d2f56ab8a806a16f8072c7752a1d3225fa624954671f87a),
código 0xac30..0xbf00 e callback 0xad78. A primeira execução entrou, mas faltou
o destino 0xb9a0. O código limita o índice a 0..6 e usa os sete offsets da
tabela em 0xb97c; foram acrescentadas as quatro entradas ausentes, sem executar
a tabela como instruções. Código do snapshot coincide com o original.
Build aprovado. Em 1792882460964832500, o boot avançou até 57,797 s e parou
no NID 0xe7fa820b (cellSaveDataEnableOverlay), LR 0x134db58, thread 23.
64 saídas AssetStream passaram. A captura final contém 5.054.464 amostras,
319.335 não zero, todas finitas, pico absoluto 0,561273. Isso prova sinal na
saída nativa, não fidelidade auditiva ou sincronização. Os frames 1001..1901
mudam: transição preta e logo animado, com artefatos visuais evidentes. Menu,
partida, saves e progressão continuam pendentes. Próximo: implementar o contrato
void de EnableOverlay com estado real e ABI correta, sem simular um save.

## Preferência de overlay de saves e ABI void

O NID 0xe7fa820b foi identificado por hash do nome cellSaveDataEnableOverlay
na fonte RPCS3 aa9ebd2f (cellSaveData.cpp). Implementado o estado atômico local
ao processo: desabilitado inicialmente, qualquer s32 não zero habilita. Um
wrapper de contexto preserva os registradores, sem passar pelo adaptador de
retorno inteiro e sem iniciar operação de save/callback. Há consulta somente
host para futura interface de seleção; essa interface ainda não foi validada.
A regressão no dispatcher real falhou com exit 90 antes e passou depois.
Sete casos cobrem sinal, truncamento s32 e ABI. 32 testes de boot, 53 do projeto,
16 CTest do runtime e builds de boot/jogo passaram. Próximo: repetir o boot.
Referência: https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/Modules/cellSaveData.cpp

## Tela de título original

Após EnableOverlay, a execução 1792902016004434800 permaneceu ativa até o
timeout de 120,239 s, sem nova falha estrita. O frame 3301 foi inspecionado:
tela FIFA STREET, Messi, texto PRESS START BUTTON e licenciamento original,
1280x720, 39 draws. Captura privada savedata-overlay-frames/frame_07,
SHA a0ce11559961bcb55cd1c85bf425a0e53224ca385ecd13861cdf0a1f91bbe213.
As 64 saídas AssetStream passaram. O mix contém 10.490.880 amostras, 699.913
não zero, nenhuma não finita; fidelidade auditiva e sincronia não validadas.
Os relatórios de checkpoint/assets foram atualizados com essa tentativa.
Próximo: Start pela entrada real e navegação. A tela de título não demonstra
menu navegável, partida ou saves; a animação anterior ainda tem artefatos.

## Entrada por arquivo preservada até um pacote válido

Em 1792902161486793500, o backend leu Start, mas a navegação não foi
confirmada antes do timeout de 180,265 s. A investigação encontrou um defeito
independente no PAD_FILE: o contador da pressão avançava também quando len=0,
podendo descartar uma pressão curta sem entregar nenhum pacote. A fixture no
cellPad real reproduziu exit 6 antes da correção. O contador agora avança
somente em relatório entregável; o modo diagnóstico always-change mantém sua
semântica e libera o botão. Os dois cenários passaram. 34 testes de boot,
55 do projeto, 16 CTest e ambos os builds passaram. A correção não comprova
sozinha a navegação do jogo; a próxima tentativa continua a partir da tela real.

## Entrega de Start e entrada no decoder EA Layer 3

Em 1792902630517693800, Start foi entregue após a tela de título e a execução
parou 0,3 s depois na entrada do decoder EA Layer 3, em 0x8938. Foram conferidos
0xdc80 bytes da fonte 0x1fa5880; SHA ff7799a9e3388eb3aec9bbedb4c7d564053067637becae38ab20422fcf3418e0.
Código termina no retorno de 0x14964; dados a partir de 0x14968 permanecem
fora da tradução. Callback 0xa250 vem do offset 0x1bd0 construído na entrada.
569 funções compiladas, nenhuma instrução ou destino direto ausente.
Em 1792902912263552700, Start foi enfileirado uma vez após comparação exata
com uma captura de título já inspecionada. Houve entrada real no decoder em
0x8680; a próxima falta, após 59,600 s, foi spugain, base 0x16580, fonte
0x1fbec80, 0x690 bytes iguais ao original. Entrada não comprova decodificação
completa. Menu navegável e partida continuam pendentes.

## Gain compilado e probe de título reproduzível

Adicionado spugain, fonte 0x1fbec80, 0x690 bytes conferidos, código
0x165b0..0x16c10 e callback 0x16638. A tabela de sete offsets em 0x16b8c,
limitada por índice 0..6, fornece as quatro entradas extras 0x16bb0, 0x16bc8,
0x16be0 e 0x16bf8. Geração sem instruções/destinos diretos ausentes e build
completo aprovado. Entrada de gain ainda não observada.
tools/run_title_probe.py reproduz o teste: pastas novas, capturas reais,
comparação exata com BMPs já inspecionados, uma pressão Start e metadados.
Não sobrepõe diagnósticos existentes nem declara sucesso pelo botão enfileirado.
A tentativa 1792903152592166400 conferiu o título e leu Start, mas terminou
por timeout de 240,306 s sem validar navegação. A correlação entre Start e a
carga do decoder nas tentativas anteriores não substitui essa validação.
A investigação seguinte reproduziu a sobrescrita indevida do payload de um
pacote de controle len=0; sua correção está em validação separada.

## Payload preservado em leituras de controle sem mudança

O teste nativo confirmou que cellPadGetData escrevia todo o array de botões
mesmo com len=0. A referência RPCS3 aa9ebd2f/cellPad.cpp atualiza esse payload
somente em relatórios válidos. A correção mantém a escrita de len e preserva
os demais bytes quando não há relatório. O teste falhou antes (exit 10) e passou
depois. A suíte completa também expôs uma suposição imprecisa na fixture anterior:
Sleep(8) nem sempre fazia o relógio de polling do Windows avançar. O teste agora
aguarda um relatório de verdade, com limite, em vez de presumir o tick.
35 testes de boot, 56 do projeto, 16 CTest e ambos os builds passaram. Nova
tentativa de título em andamento; a correção ainda não demonstra menu navegável.

## Telemetria do pacote de controle entregue

PAD_REPORT_TRACE registra até 64 transições de botões em relatórios válidos,
após as escritas no buffer guest. Campos: sequência, porta, endereço, len,
modo e digitais; desligado por padrão e sem alterar o estado do jogo. Os testes
de pressão/liberação falharam sem o log e passaram com os eventos estruturados.
35 testes de boot, 56 do projeto e ambos os builds passaram.
Na tentativa 1792904083852197000, o jogo recebeu Start na porta 0, buffer
0xd0189ce0, len=24, modo 0x7c, digital1=8, depois digital1=0. Processo ativo até
timeout de 180,180 s, sem nova falha estrita e sem navegação validada. O pacote
chega ao handler PPU que chama GetData em LR 0x14351d0. Próximo: conferir a
transformação desse pacote em estado de botões, incluindo o bitset VMX original.

## Função original de bits/pressão conferida

O probe --test-fifa-input-bitset executa a função traduzida original 0x1434db8
pelo dispatcher público do executável completo. 384 casos combinam índices
0..63 e seis valores, cobrindo bits digitais, bytes de pressão, truncamento,
índices fora do intervalo, preservação dos demais bytes e da stack. Todos
coincidiram com o oráculo de bits/bytes. Não é conformidade completa da PPU
nem prova da leitura do botão pela interface. 35 testes de boot, 57 do projeto
e ambos os builds passaram. Próximo: confirmar o comportamento visual com
entrada de confirmação, sem alterar flags internas ou pular a lógica do jogo.
