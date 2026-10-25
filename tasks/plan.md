# Plano de continuidade: FIFA Street nativo no Windows

## Escopo

Implementar o port offline de FIFA Street PS3 BLUS30882 01.00 para Windows x64.
O prompt completo, incluindo requisitos e critérios de conclusão, está em
`../PROMPT_EXECUCAO_COMPLETA.md`. Este plano ordena a próxima execução; não relata
integrações ainda inexistentes.

## Base validada anteriormente

Commit `e96e614`: extração dos dois SELF, obtenção dos ELF, loader PPU, duas funções
traduzidas com 20.020 retornos testados e 16 testes do runtime aprovados.
Jogo, boot, gráficos e partida ainda não validados. Reproduzir antes de implementar.

## Avanço validado em 24/10/2026

Baseline reproduzido. Commits `29faa79`, `247aae2`, `774a345`, `8469e05`,
`8ade95c` e `c90424b` registram o boot real, a extração completa, a troca nativa
EBOOT -> FIFAZF, os diagnósticos e o registro dos exports reais de três
bibliotecas CRT. O FIFAZF já criou threads e consultou o conteúdo do jogo.
Seis testes do boot passaram. O estado detalhado está em `STATUS.md`;
primeiro frame, menu e partida continuam sem validação.

A integração de jump tables passou no teste sintético e o jogo ultrapassou
`0x432cc -> 0x43738`, chegando à inicialização GCM. O incremento em andamento
liga os callbacks HLE ao dispatcher e o consumidor FIFO/relógio RSX ao host.
Aceite: argumentos/identidade de callback preservados; janela D3D12 inicializada
no hardware local; o FIFO avança por comandos reais, com próximo resultado
registrado. Um flip/uma janela ainda exigem validar a imagem do jogo.

## Decisões

- Reutilizar o repositório existente e a revisão fixada de ps3recomp.
- Manter PS3 como entrada; ReStreet é referência de outra plataforma.
- Manter dados e código derivado do jogo em `private/`.
- Versionar adaptadores próprios, scripts, testes e patches de dependências.
- Avançar por código real executado e estados observáveis do jogo.
- Escolher integrações concretas após ler o runtime; não presumir um backend completo.

## Ordem e critérios

| Etapa | Depende de | Aceite | Verificação |
|---|---|---|---|
| Reproduzir baseline | Arquivos locais e toolchain | Build e testes anteriores reproduzidos | `tools/build.ps1`, hashes e logs |
| Revisar fluxo de boot | Baseline | Entradas, argumentos, módulos e contexto identificados | Evidência de bytes, chamadas e imports |
| Preparar loader nativo | Fluxo de boot | Segmentos, BSS, stack, TLS, TOC e OPD coerentes | Testes de memória e contexto |
| Executar startup PPU | Loader | Caminho real executado com primeiro bloqueio rastreável | Trace de módulo/endereço/chamada |
| Completar serviços do startup | Trace | Caminho necessário sem resultados fabricados | Testes de handlers e novo trace |
| Integrar tarefas SPU alcançadas | Inventário e startup | DMA/canais/resultados e sincronização corretos | Comparação de dados e progresso do jogo |
| Renderizar frame original | Startup e dados | Frame produzido pelo jogo | Captura com cenário e logs de RSX |
| Navegar nos menus | Frame e serviços | UI original responde a entradas | Navegação observada e registrada |
| Completar partida | Menus, SPU, gráficos e entrada | Jogo interativo do início ao fim | Roteiro de partida e registros |
| Validar saves e progressão | Partida | Estado persiste após reiniciar | Gravar, fechar, abrir e retomar |
| Ampliar conteúdo offline | Fluxos básicos | Matriz de modos e conteúdo validada | Cenários por modo/arena/fluxo |
| Medir estabilidade e desempenho | Gameplay | Sem falhas críticas nos cenários medidos | Sessões repetidas, perfis e frametimes |
| Reproduzir instalação | Integrações completas | Checkout limpo e dados locais geram jogo funcional | Build/execução fora da pasta de desenvolvimento |

Cada linha representa uma frente que deve ser dividida em incrementos pequenos
antes de editar. Para cada incremento, identificar arquivos exatos, dependências,
até três critérios de aceite e teste correspondente. Priorizar 1–5 arquivos por
mudança; subsistemas grandes não devem virar um único patch.

## Checkpoints

1. Fundação: baseline, fluxo de boot e primeira inicialização rastreada.
2. Apresentação: primeiro frame e menu reais.
3. Gameplay: primeira partida completa e retomada de save.
4. Cobertura: matriz offline, estabilidade e instalação reproduzível.

Cada checkpoint exige evidências e commit. Somente o quarto, com todos os
requisitos obrigatórios cobertos, permite avaliar a declaração de port completo.

## Riscos concretos

| Risco | Tratamento |
|---|---|
| REA não admite ELF64/PPC64 na versão instalada | Usar ferramentas compatíveis; manter diagnóstico original |
| Contagem de imports confundir nomes com implementação | Auditar biblioteca/NID, ABI, wrappers e comportamento |
| Lifter ou runtime apresentar stubs silenciosos | Diagnóstico explícito e validação do caminho necessário |
| Arquivos ISO de múltiplos extents serem truncados | Preservar todos os extents no extrator completo |
| SPUs ou renderizador exigirem trabalho específico | Descobrir cedo os caminhos alcançados e validar separadamente |
| Mudanças em vendor ficarem fora do histórico | Patch versionado ou fork fixado, aplicado no bootstrap |
| Dependência não documentada do PC do desenvolvedor | Preparação e build testados em checkout limpo |

Não há estimativa confirmada para finalizar o jogo. Bloqueios e decisões futuras
devem ser registrados no `STATUS.md` pelo agente que iniciar a implementação.

## Incremento SPU multi-segmento

Pipeline e registro nativo de 14 imagens integrados; seis recusadas explicitamente.
Doze testes de geração, sete de boot e 16 do runtime aprovados. A tentativa estrita
`1792839751667270900` alcança a imagem inicial e para em salto para `0x3f00c`.
Antes de expandir sua cobertura, verificar por que três grupos distintos iniciam
a mesma thread `0x2000`; isso pode compartilhar e corromper seu contexto nativo.
Nenhum resultado de tarefa, frame ou gameplay aceito por esse incremento.

O mapeamento de números SPU foi corrigido e aprovado em teste Windows dos handlers
reais: três grupos, quatro threads, números não contíguos e argumentos preservados.
O teste falhou antes da correção (quatro visitas à primeira thread) e passou
depois. Oito testes de boot e 16 do runtime aprovados; validação no jogo pendente.

A correção foi confirmada no jogo com seis threads distintas. A descoberta PPU
passou a revisitar ranges divididos; 351 entradas adicionais e zero referências
diretas pendentes na geração completa (99.127 + 369 imports). Três regressões
sintéticas passaram. O rebuild executou até consultas Lua e salto SPU em LS
`0x100`; capturar o código residente antes de decidir qual imagem traduzir.

O boot passou a carregar DATA0 após preservar o nome UDF. RefPack, mixer,
submix PIC e sample capture foram ligados progressivamente. Foram comparadas
47 saídas nativas AssetStream contra oráculos independentes, com igualdade
byte a byte. O próximo bloqueio observado é spugainfader em LS 0x6bb0;
primeiro frame desenhado, menu, áudio e gameplay continuam pendentes.

O DAC passou até a consulta NP, que agora informa corretamente o estado offline.
O primeiro frame com desenho foi conferido visualmente (logo FIFA Street).
Não há menu aceito. Investigar a progressão após o logo com amostras de threads
e entrada de controle explícita; não inferir travamento apenas do timeout.

A espera em Readdir foi reproduzida: o jogo usa d_type como sentinela de EOF.
O adaptador agora reproduz a distinção HDD0/HDD1 observada na referência.
Os quatro cenários Windows passam, e DLC saiu desse loop no novo boot.
Investigar o carregamento seguinte sem forçar a flag de inicialização do jogo.

Os módulos pause, resample e rechannel foram ligados e suas entradas alcançadas.
A sobreposição parcial de imagens SPU exigiu intervalos de código disjuntos;
regressão antes/depois aprovada, 22 testes de boot e 16 do runtime. O próximo
PC estrito é 0x5970 na thread de áudio; identificar e recompilar o residente.

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

## Plano AOT PIC relocável

Contrato: tasks/spu-relocatable-pic.md. Primeiro ownership/registro e teste
Windows com dois endereços simultâneos; depois emissão e fixture SPU autoral
compilada em três bases; depois configuração/geração; por último entrada real
do sound player 1 em LS 0x7800. Manter a flag desligada até passar os checks.
O deslocamento será local a cada função; não adicionar base global mutável.
A decisão preserva os requisitos AOT e de falha explícita já autorizados no
PROMPT_EXECUCAO_COMPLETA.md. Não há nova etapa de aprovação necessária.

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

## Emissão PIC verificada

Concluída a segunda etapa do contrato: emissão de endereços relativos com
deslocamento local e fixture SPU autoral traduzida para x64. Oito execuções
em quatro posições passaram, incluindo links físicos, memória absoluta/relativa
e callback entre programas. BRA/BRASL são recusados. 30 testes de boot e o
build completo passaram; as 37 fontes antigas ficaram idênticas com a opção
desligada. O baseline real 1792881874546096800 parou em LS 0xb300 após 21,825 s;
a concorrência muda a cadeia observada. Próximo: integrar o manifesto e medir
uma entrada PIC real fora das posições estáticas já existentes.

## Gerador PIC optativo integrado

Concluída a terceira etapa: flag booleana explícita, validação do cabeçalho e
entrada relativa, uma imagem canônica e registro PIC com fingerprint. Os testes
de manifesto passaram e a regeneração com flag desligada preservou 39 arquivos
byte a byte (37 fontes SPU, registro e lista CMake). Próxima etapa: habilitar
somente sound player 1, compilar e registrar a entrada física real. A ordem de
agendamento pode exigir várias observações; não admitir posição por previsão.

O observador passou a deduplicar por programa e base física, com bitmap limitado
à LS. A regressão falhou antes e passou depois; 31 testes de boot, 52 do projeto
e ambos os builds passaram. Isso permite conferir posições relocadas reais,
sem inferir entradas que o log anterior ocultava.

## Entrada real relocada do sound player

Com relocatable_pic habilitado somente no sound player 1, a tentativa
1792882100622595900 entrou em base 0x7800 sem variante estática. O bloqueio
seguinte, PC 0x7b60, pertence ao decoder PCM float carregado em 0x7680;
não adicionar entrada ao sound player por simples aritmética. Fonte 0x1fa3a00,
0xb80 bytes, conferida contra o snapshot. 64 saídas AssetStream passaram.
Próximo: admitir o código original desse decoder e habilitar PIC nos módulos
de áudio já auditados. Menu e áudio ainda não validados.

## Ampliação PIC e próximo módulo real

Treze módulos PIC e 18 registros totais compilados, sem operações/destinos
diretos ausentes. O mixer permaneceu fixo por layout distinto. A execução
1792882263069156500 validou entrada do decoder PCM float e novas bases de
vários módulos (submix 0xb300 entre elas), depois faltou spusend em 0xac30.
Seu blob 0x1400, fonte 0x1fc4b80, coincide com o original. Próximo: conferir
limites/callbacks e traduzir esse módulo. Captura tardia continua no logo e
áudio final continua zero; não marcar menu/áudio como resolvidos.

## Send verificado e próxima dependência HLE

Send e quatro destinos da tabela limitada de sete entradas foram traduzidos.
Em 1792882460964832500, o jogo avançou até cellSaveDataEnableOverlay, NID
0xe7fa820b, com 64 saídas AssetStream corretas. Há agora sinal finito não zero
no mix final, sem validação auditiva/sincronia. Os frames mudam, mas o logo
animado tem defeitos. Próximo: estado de preferência de overlay e wrapper
void conforme RPCS3 fixado; não confundir essa chamada com gravação de save.

## EnableOverlay implementado e validado isoladamente

Estado atômico por processo e wrapper de contexto void integrados ao SDK/patch.
A regressão do dispatcher real falhou antes e passou depois. Sete valores de
entrada conferem truncamento s32, preferência e preservação de registradores.
32 testes de boot, 53 do projeto, 16 CTest e os dois builds passaram. Boot real
com timeout 120 s em andamento para identificar a próxima dependência.

## Tela de título conferida

Em 1792902016004434800 o frame 3301 mostra a tela original PRESS START BUTTON,
com Messi e licenciamento. Processo ativo até timeout 120,239 s, sem nova
falha estrita. Relatórios atualizados; 64 saídas AssetStream passaram e há
sinal finito no áudio. Próximo: pressionar Start pela entrada PAD_FILE após
conferir a tela na nova tentativa. Não usar uma sequência cega de confirmações.

## Entrega de Start em pacotes válidos

A tentativa 1792902161486793500 leu Start no backend, mas não validou menu.
Fixture nativa demonstrou que PAD_FILE consumia pressões em leituras len=0.
Corrigido para decrementar somente em relatório válido, mantendo o modo
always-change. A regressão falhou antes e passou depois; 34 testes de boot,
55 do projeto, 16 CTest e ambos os builds passaram. Próximo: repetir a entrada
após inspecionar a tela de título e observar o resultado, sem presumir avanço.

## EA Layer 3 admitido após Start

Após Start, observou-se a carga do decoder EA Layer 3. Fonte 0x1fa5880, tamanho 0xdc80,
conferidos com o snapshot; código 0x86b0..0x14968, callback 0xa250. 569 funções
compiladas sem operações/destinos diretos ausentes. A tentativa
1792902912263552700 confirmou a entrada e parou no próximo módulo, spugain
em 0x16580. Próximo: traduzir seu código e a tabela limitada de sete valores
em 0x16b8c. Não tratar a carga de áudio como prova de menu ou partida.

## Gain e repetição controlada do título

Gain foi conferido e compilado, incluindo callback e quatro casos da tabela
limitada. A entrada ainda precisa de observação. Novo comando reproduzível:

```powershell
private/python-env/Scripts/python.exe tools/run_title_probe.py --label nova-tentativa --title-reference private/analysis/savedata-overlay-frames/frame_07/backbuffer.bmp --title-reference private/analysis/start-fresh-frames/frame_05/backbuffer.bmp
```

Os BMPs são referências privadas já inspecionadas. O probe só enfileira um
Start após coincidência exata e recusa um label já usado. A tentativa gain
1792903152592166400 completou o diagnóstico em 240,306 s sem nova falha,
mas também sem menu validado. Próximo: corrigir payload de controle len=0
conforme a fonte fixada; reprodução nativa já confirmou a divergência.

## Preservação de payload len=0

cellPadGetData agora escreve apenas len quando não tem relatório, preservando
os botões no buffer guest. Reprodução falhou antes com exit 10 e passou depois.
A fixture de pressão pendente passou a aguardar um relatório real, corrigindo
uma suposição sobre Sleep(8)/tick do Windows exposta pela suíte completa.
35 testes de boot, 56 do projeto, 16 CTest e ambos os builds passaram. Próximo:
avaliar a tentativa pad-payload, que compara o título e envia um Start.

## Pacote Start entregue: seguir o handler PPU

pad-payload terminou por timeout 240,299 s, sem validar menu. O diagnóstico
PAD_REPORT_TRACE foi adicionado e testado (35 boot/56 projeto, builds aprovados).
Em 1792904083852197000, Start e liberação foram gravados em relatórios válidos
de 24 palavras, modo 0x7c, porta 0, buffer 0xd0189ce0. Caller PPU 0x14351d0.
A questão restante é o processamento desse estado pelo jogo; não concluir
aceitação da navegação apenas pela entrega. Conferir o bitset original 0x1434db8
contra um oráculo de bits e então seguir o estado da interface.

## Bitset original verificado

384 casos da função original 0x1434db8 passaram via dispatcher do full game,
incluindo o caminho VMX de bits e o armazenamento de pressão. Não modificar
essa rotina sem nova evidência. 35 testes de boot, 57 do projeto e builds
aprovados. O teste pode ser repetido com:

```powershell
private/build/fifazf_full/fifa_boot.exe --test-fifa-input-bitset
```

Próximo: observar a tela e testar confirmação por Cross, registrando os pacotes
reais e o próximo estado. Não marcar menu como validado apenas pela entrega.

## Probe sem depender do piscar do texto

title-confirm não enfileirou entrada porque o hash integral variou com o texto
piscante (o título foi inspecionado). --title-region adiciona comparação exata
de uma área fixa revisada. Três testes com BMPs autorais passaram, totalizando
60 testes do projeto. A comparação de dois frames reais confirmou esse caso.
Em title-region, a área 70,70,720,100 autorizou Start. Cross foi enviado somente
após nova inspeção do título, às 02:11:34 de 2026-10-25. Aguardar o próximo
estado antes de confirmar qualquer outra ação.


## Pacotes de controle por modo (2026-10-25)

A referência RPCS3 aa9ebd2f, cellPad.h e pad_get_data em cellPad.cpp,
usa comprimentos 8/20/24 para padrão/pressão/sensor. O runtime usava
8/24/28 e copiava todas as 64 palavras em relatórios válidos. Corrigidos os
comprimentos e a escrita parcial: padrão também limpa pressão 8..19;
sensores 20..23 só são escritos no modo sensor; a cauda restante é preservada.
A fixture --test-pad-modes cobre as quatro combinações de flags, cabeçalhos
0x74/0x7a/0x7c e bytes sentinela. Falhou antes (exit 13, cauda sobrescrita no
modo padrão) e passou depois. Builds Boot e FullGame, 36 testes de boot,
61 testes do projeto e 16 CTest passaram. Alteração do SDK incluída no patch.
A tentativa anterior title-region terminou em timeout de 240,228 s: Start e
Cross foram entregues, mas menu não foi validado. Nova tentativa pad-protocol
verificará o pacote corrigido no fluxo real; esse teste isolado não prova
navegação ou gameplay.


## Filtro de áudio highpass após ganho (2026-10-25)

pad-protocol (1792905620222926300) chegou ao título e encerrou por falta
estrita em 53,283 s, PC SPU 0x16cb0. Entradas reais de EA Layer 3 e spugain
foram registradas, incluindo ganho em LS 0x16580. O próximo programa em
LS 0x16c80 é spuhighpassiir2.elf: cabeçalho único no ELF, origem 0x1fbf380,
0xb20 bytes, SHA c135ec6c9ca9ae3e391f16bdc3c92f997b959fe45f8de96af800fa592b8053e9,
zero diferenças contra todo o blob residente. Código 0x16cb0..0x17798,
callback construído em base+0xb8 (0x16d38). A tabela em 0x17714 tem sete
entradas e guarda clgti >6; adicionados seus quatro destinos não detectados
0x17738/0x17750/0x17768/0x17780. Os zeros finais e a área de dados/BSS
não foram admitidos como código. 28 funções, zero instruções sem suporte,
zero destinos diretos ausentes; FullGame compilou e 61 testes passaram.
Tentativa highpass em andamento. O Start foi enfileirado após o título no
run anterior, mas a falha concorrente ocorreu antes do log de pacote válido;
ainda falta comprovar esse pacote corrigido no jogo e o menu navegável.


## Estado original após entrada e observador optativo (2026-10-25)

Em input-state (1792906104246235100, timeout 180,176 s, sem falha estrita),
o pacote Start len=20/header=0x7a foi seguido pelo estado original: manager
275468744, device 275322876, quatro controles digitais, bitset 275976300.
O bitset passou de 0 para 8 e voltou a 0, e manager+0x58 de 0 para 0x00080000
e de volta a 0. Isso comprova o processamento do pacote pela rotina PPU,
mas ainda não a aceitação pela interface. Menu e partida seguem pendentes.
A execução highpass anterior terminou em timeout de 180,187 s sem nova falha;
a entrada do highpass não foi observada nessa tentativa.

FIFA_INPUT_TRACE instala, apenas quando pedido, um wrapper de GetInfo2 que
chama a API real e observa o estado da atualização ANTERIOR no caller revisado
0x1434eb0. JSON limitado a 64 transições, com thread/endereços/status/bits e
pressão de Cross. Leitura limitada a páginas já comprometidas, sem tocar
páginas ausentes, alterar flags do jogo ou modificar o código gerado.
A fixture nativa confere ligado/desligado, deduplicação, retorno real, GPRs,
memória observada, dispositivo inválido, caller distinto e pressão/liberação.
O caso de pressão falhou antes (campo Cross ausente) e passou depois.
37 testes de boot, 62 do projeto e builds Boot/FullGame aprovados.
A primeira tentativa de relink com EBOOT ainda ativo falhou por arquivo em uso;
após o fim do run, a compilação e os testes foram concluídos normalmente.
Próximo: input-pressure, conferir Cross real e os leitores do bitset, com
PPU_RWATCH no endereço confirmado; se o endereço variar, reavaliar o watch.


## Correção do observador de Cross (2026-10-25)

A revisão dos offsets do handler 0x1434e6c identificou um erro no diagnóstico:
Cross é lido de button[14] (stack+0x90), escrito no controle 14 e convertido
pelo setter em índice de pressão 10, pois o dispositivo tem quatro digitais.
O observador anterior lia índice 9 (Circle). Corrigidos observador e fixture;
37 testes de boot, 62 testes do projeto e build FullGame passaram. No run
input-pressure 1792906410038970600 (180,181 s, timeout), Start e Cross foram
entregues em pacotes len=20/0x7a, mas o campo cross_pressure daquele run mede
Circle e NÃO comprova falha nem sucesso da pressão de Cross. A leitura real
pelos consumidores passa por 0x1435ab8/0x1435a4c, com caller 0x11aa178.
O host-sampled guest-fn 0x1431ef4 é ambíguo por folding de código; usar o LR
e a cadeia de chamadas. Menu permanece não validado.


## Conversão e vínculos originais de entrada (2026-10-25)

O probe --test-fifa-input-sampler executa 0x11aa178, incluindo as consultas
0x1435ab8/0x1435a4c e o dispatcher 0x11a9ee0. Usa dispositivo autoral com o
layout real (4 digitais/12 pressões), constantes exatas conferidas no ELF e
provedores de metadados autorais restritos ao teste. Os 112 casos combinam
16 máscaras digitais e sete pressões; 1.792 valores normalizados e 224 ações
lógicas Start/Cross conferem com oráculos independentes. Provedores e vínculos
sintéticos não são instalados no boot do jogo. Não é teste de eventos da UI,
nem conformidade completa da PPU. Ambos os builds e 63 testes do projeto
passaram antes da adição do inspetor de memória, cujos dois testes são separados.


## Inspeção de memória nativa sem escrita (2026-10-25)

tools/inspect_native_memory.py aceita somente o PID cujo executável é o
FullGame deste projeto. Abre QUERY_INFORMATION|VM_READ; resolve vm_base pelo
PDB local e seções PE, sem attach de debugger, chamadas remotas ou escrita.
Até 16 leituras de no máximo 4 KiB, limitadas ao espaço guest. Snapshots não
são atômicos: threads continuam executando. Dois testes verificam offset
decimal do símbolo e limites; 65 testes do projeto passaram. Leitura real no
PID 3580 confirmou o ponteiro do provedor de bindings 0x2259690 -> 0x106f09f0,
o dispositivo (4 digitais/12 pressões/8 eixos) e seus buffers, coerentes com
a telemetria. Nova leitura após o processo encerrar falhou, sem fabricar bytes.
O run native-bindings 1792935048107759000 terminou em 76,152 s por falta SPU
em 0x17830: highpass entrou de verdade; próximo programa é lowpass. A inspeção
é diagnóstico e não prova de navegação. Dumps continuam em private/.


## Lowpass nativo e execução sem teclado (2026-10-25)

spulowpassiir2 foi identificado na falta estrita de native-bindings:
origem 0x1fbff00, 0xb10 bytes, SHA c202671ae8a6a3485ba64d10caa956f5eeefc9a287ef47973ecf21a4a22b1d63,
residente em LS 0x17800 com zero diferenças. PIC, entrada 0x17830,
código até 0x18310; callback base+0xb8 e quatro destinos da tabela de sete
casos em 0x1828c com guarda >6. Tradução de 28 funções, sem instruções
sem suporte/destinos diretos ausentes; FullGame compilou e 65 testes passaram.
lowpass (1792935306961542300) terminou em timeout de 240,336 s sem nova falta,
sem entrada observada desse filtro e sem menu validado. PAD_NO_KEYBOARD=1
isolou a entrada; o run anterior tinha registrado teclado ativo, portanto sua
segunda pressão de Start não deve ser atribuída ao driver de arquivo.
As leituras reais confirmaram 48 bindings de PS3 Controller; os vínculos
19 -> VB_FE_START (38) e 30 -> VB_FE_SELECT (29) estão presentes.
Dumps do provedor, tabela e funções examinadas estão em private/analysis.


## Entrada após título estável e isolamento do teclado (2026-10-25)

O probe agora desabilita teclado por padrão (PAD_NO_KEYBOARD), aceita duração
limitada --hold-reports 1..300 e --title-delay 0..20. A decisão usa somente a
captura mais recente, ordenada pelo número do frame; arquivo já conferido não
faz o timer avançar. Uma nova captura completa precisa continuar correspondendo
ao título. Um frame diferente reinicia a espera; capturas antigas não autorizam
entrada sobre outra tela. A fixture de atraso falhou sem TitleGate e passou
depois; quatro testes de captura e 66 testes do projeto passaram. O driver não
afirma aceitação pela UI a partir da comparação ou do pacote.
held-start (1792935757553539400, 180,213 s) manteve Start por 250 relatórios,
sem nova falta ou menu confirmado. A amostragem externa do contexto principal
não capturou os LRs desejados antes do fim do processo; sua leitura incompleta
não é evidência de valores de entrada. delayed-start (1792935993680801600)
enviou Start após sete segundos de capturas de título e parou em 61,488 s por
falta em 0x1d5b0. Lowpass entrou de fato, seguido por send/genericplayer/
packetplayer/submix em novas bases PIC. Isso é avanço do caminho de áudio,
não prova isolada de que a UI aceitou Start. Próxima rotina: highshelf IIR.


## Highshelf IIR nativo (2026-10-25)

Falta estrita em 0x1d5b0 identificada como spuhighshelfiir2.elf, origem
0x1fe1d80, 0xcc0 bytes, SHA eaf44927abb46f39fe530b3aa45226a633681cfb28c6e729410c8ad54eb9418e.
Todo o blob residente em LS 0x1d580 coincide com o original. Código
0x1d5b0..0x1e240, callback base+0xb8 em 0x1d638. A tabela em 0x1e1bc,
guardada por clgti >6, exige também 0x1e1e0/0x1e1f8/0x1e210/0x1e228.
32 funções traduzidas, zero instruções sem suporte/destinos diretos ausentes,
FullGame compilou e 66 testes passaram. A tentativa highshelf usa o probe
corrigido (capturas novas, atraso mínimo de sete segundos) e está em andamento;
entrada do highshelf e navegação ainda não validadas.


## Lowshelf IIR nativo (2026-10-25)

highshelf (1792936203143744000) executou esse filtro e terminou em 59,540 s
com falta estrita no PC 0x1e330. O programa seguinte spulowshelfiir2.elf
coincide integralmente com a origem 0x1fe9500, 0xcc0 bytes, SHA
5bf94a472ae8815850fd03343ff9e4c3dd486e0c8e79ca578805428ee96a2dd5.
Admitido PIC em base 0x1e300, código 0x1e330..0x1efc0, callback 0x1e3b8.
A tabela 0x1ef3c tem sete casos e guarda >6; destinos extras
0x1ef60/0x1ef78/0x1ef90/0x1efa8. 32 funções, sem instruções sem suporte ou
chamadas diretas ausentes; FullGame e 66 testes passaram. Run lowshelf em
andamento com a mesma entrada após sete segundos de título estável; entrada
do lowshelf e próximo estado ainda pendentes. Não há menu ou partida validados.


## Peaking IIR nativo (2026-10-25)

lowshelf (1792936374268589100) terminou em 59,561 s com falta estrita
0x1f2e0; lowshelf entrou de fato. A origem seguinte é spupeakingiir2.elf,
EA 0x1ff3580, 0xd10 bytes, SHA dcdb50f6dcabc6a849239d8ca21cb1bef40c7b6dd6451964dceaa443fe73eed4,
zero diferenças em LS 0x1f080. A entrada do cabeçalho é base+0x260 (0x1f2e0),
e não base+0x30: a rotina matemática anterior também é código original.
Limites 0x1f0b0..0x1fd88, callback 0x1f368 e casos indiretos
0x1fd28/0x1fd40/0x1fd58/0x1fd70 da tabela 0x1fd04 guardada por >6.
Tradução sem instruções sem suporte/destinos diretos ausentes; FullGame
compilou e 66 testes passaram. Run peaking em andamento; aguardar entrada
real e próximo estado, mantendo menu/partida/saves como não validados.


## Limitador de áudio nativo (2026-10-25)

peaking (1792936566408202600) executou esse filtro e encerrou em 59,333 s
com falta estrita 0x1fe30. O residente é spulimiter1.elf, origem 0x1fe2e80,
0x36b0 bytes, SHA a7c9bdaa9048d197be30109177638b2a601a0617f15cbc89cabfb6b08aac788b,
coincidência integral em LS 0x1fe00. PIC, entrada/código 0x1fe30,
limite 0x234a8 antes dos zeros de padding. Callback do construtor em
base+0x398 = 0x20198; tabela guardada de sete casos em 0x230fc exige
0x23120/0x23138/0x23150/0x23168. Chamadas indiretas ao kernel permanecem
no dispatcher estrito. Sem instruções sem suporte/destinos diretos ausentes;
FullGame e 66 testes passaram. Run limiter em andamento, sem afirmar execução
ou menu apenas pelo link. Os dados e código gerado continuam privados.
