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

Há 14 ELFs SPU e 14 programas raw ligados, mais cinco posições PIC
adicionais compiladas estaticamente (19 registros raw no total). Submix,
sample capture, gain fader e VU meter passaram pelas segundas posições
observadas. A execução 1792871899123215200 chegou a 90,238 s sem nova
fronteira estrita; ainda no logo, sem menu aceito.
A amostra posterior 1792872007341002900 mostra main esperando mutex 8,
LR 0xdce220. Ainda falta identificar seu dono e a dependência da espera.
A captura de 1.542.656 floats do mix de áudio é inteiramente zero: áudio audível
continua pendente. 24 testes de boot passaram após a correção NetCtl abaixo;
o teste integrado alcançou a segunda carga do DAC, e as 47 saídas de assets
continuaram iguais às referências. A espera amostrada não prova deadlock.

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
