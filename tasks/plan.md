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


## Panoramização nativa e seis tabelas de salto (2026-10-25)

limiter (1792936791296985800) executou o limitador e encerrou em 59,392 s
no PC 0x165b0. Esse endereço agora continha spupan2d1.elf, não o ganho
anterior: origem 0x1fc0a80, 0x40c0 bytes, SHA
44a31088831991f57ad403182038cef0a9ca1d2cfaeefa98281f50b76ca0fcd5,
zero diferenças contra o blob residente em LS 0x16580. A invalidação do código
antigo evitou executá-lo sobre o novo programa. PIC, código 0x165b0..0x1a638,
callback construído base+0x718 = 0x16c98.
O primeiro build admitiu quatro tabelas; pan (1792937112328856700, 59,628 s)
entrou de verdade e parou em 0x18328, LR 0x16ee8. A revisão de TODOS os BI
não-r0 identificou seis tabelas de sete casos, guardadas por >6:
0x17b3c, 0x17d0c, 0x181ac, 0x19c8c, 0x1a09c, 0x1a5b4. Incluídos todos os
seus destinos assinados, inclusive retornos compartilhados e saltos para trás.
A falta observada pertence à tabela 0x181ac; não houve bypass da instrução.
FullGame compilou, a tradução não tem instruções sem suporte ou destinos
diretos ausentes e 66 testes passaram. Run pan-cases em andamento com sete
segundos de título e 250 relatórios de Start; menu ainda não validado.
A análise dos threads confirma FEThread=23, RenderThread=22 e InputThread=24;
a amostragem anterior do contexto principal não representava a thread de UI.


## Avanço real da UI e espaço livre do HDD (2026-10-25)

pan-cases (1792937375655805500, timeout 180,215 s) ultrapassou os saltos
anteriores e executou pan2d1 também em LS 0x8680. A captura frame_11
(frame_count=4321, 53 draws) mostra o diálogo ORIGINAL INFORMATION, informando
que faltam pelo menos 1024 KB no HDD. É avanço real após Start, mas não menu,
partida ou save validado. Captura: private/analysis/pan-cases-frames/frame_11.
O disco D tinha cerca de 519 GB disponíveis; a hipótese passou à consulta
libfs e ao fluxo de armazenamento, sem alterar a mensagem ou o estado do jogo.

O handler de contexto cellFsGetFreeSize devolvia 32 GiB fixos. A fixture
--test-fs-free-space compara o retorno com GetDiskFreeSpaceExA antes/depois
no volume montado: falhou (34.359.738.368 vs cerca de 10,4 GB no volume C do
teste). O handler agora usa filesystem::space.available, com blocos virtuais
de 4096 bytes e count u64 BE. Argumentos nulos retornam EFAULT sem tocar os
outputs; falha no host retorna erro com outputs zerados, sem espaço inventado.
As raízes bare /dev_hdd0 e /dev_hdd1 passam a respeitar seus overrides: antes
só o prefixo com barra final respeitava o mount, levando a outra unidade.
Teste adicional cobre mount host ausente. 39 testes de boot, 68 do projeto e
FullGame passaram; alteração do SDK foi incluída no patch e revisada.
Referência primária: RPCS3 aa9ebd2f Modules/cellFs.cpp e lv2/sys_fs.cpp,
consultadas e guardadas em private/analysis/rpcs3-reference.

A primeira tentativa FullGame esbarrou em link porque disparei a execução cedo;
o run free-space (1792938225415918500, 61,738 s) usou a versão ANTERIOR,
foi interrompido e não valida a correção. Após finalizar essa árvore própria,
relink e 68 testes terminaram com sucesso. free-space-verified está em execução
com o executável atualizado e log do NID AA3B4BCD. A remoção do erro do jogo
continua pendente de observação; a correção de consulta não prova essa remoção.


## Rastreamento de imports e causa do aviso de 1024 KB (2026-10-25)

free-space-verified (1792938406702108300, timeout 180,205 s) manteve o diálogo;
nenhuma chamada a cellFsGetFreeSize foi observada. storage-trace
(1792938922133005500, 180,248 s) não mostrou nova operação FS após Start.
Acrescentado PS3_HLE_FIRST_CALLS, desligado por padrão, com admissão de até
4096 pares NID/LR sob mutex e argumentos/retorno registrados sem modificar a
chamada. Fixture verifica habilitação, deduplicação e preservação de outputs.
40 testes de boot, FullGame e 69 testes do projeto passaram.

storage-imports (1792939424144353700, timeout 150,299 s) mostrou BootCheck
entregando 506457284 KB livres e, imediatamente após Start,
sceNpTrophyGetRequiredDiskSpace em LR 0x1381658 devolvendo o valor fixo 1 MiB.
O serviço anuncia INSTALLED antes sem instalar o TRP; essa consulta deveria
considerar os arquivos realmente instalados. Referência RPCS3 aa9ebd2f,
Modules/sceNpTrophy.cpp e Loader/TRP.{h,cpp}, guardada privadamente. A próxima
etapa é instalar/verificar o pacote local, remover a capacidade necessária
inventada e testar os erros e o reinício. O aviso ainda não foi resolvido no
jogo e menu/partida/saves continuam não validados.


## Instalação real dos troféus e autosave original (2026-10-25)

Substituído o valor fixo de 1 MiB por leitura/verificação do TRP local.
Parser valida limites, nomes, duplicações, sobreposição e SHA-1 em versões
>=2; instalação usa diretório temporário e rename, preservando instalações
existentes divergentes. TROP.SFM fornece a configuração padrão; variantes
localizadas permanecem disponíveis, mas seleção de idioma ainda não foi
implementada. Root default acompanha PS3_HDD0_ROOT/home/00000001/trophy.
Erros de escrita não completam callbacks; progresso existente não é regravado
na inscrição. Acrescentado hook síncrono que preserva retorno real de callback
PPU (incluindo recusa), mantendo a ABI anterior das notificações void.
Corrigidos códigos de erro de troféus segundo RPCS3 aa9ebd2f sceNpTrophy.h.
Metadados, grades e desbloqueios ainda genéricos do upstream são bloqueados
explicitamente no boot estrito até terem dados e persistência verificados.

Os novos testes falharam antes da implementação (8 falhas/1 erro); passaram
após a correção. Resultado final: 41 testes de boot, seis de armazenamento de
troféus e 76 testes do projeto passaram; FullGame compilou.

trophy-installed (1792940656197898700) executou inscrição/instalação real.
Oráculo Python independente verificou 42 arquivos byte a byte contra o TRP
SHA256 cc4067e02bc54cc2a729811b21d41bf4153394b2b4e4a4ac20570a2d143e4854,
677296 bytes, versão 1, 43 entradas originais. TROPCONF é substituído pela
configuração padrão TROP.SFM; por isso 42 destinos. Consulta após Start
retornou 0 bytes necessários. O erro de HDD desapareceu; frame_10 (4201,
71 draws, 1280x720) mostra o aviso ORIGINAL de salvamento automático legível.
Após conferência visual de frame_20, um Cross (0x4000, 40 reports) foi enviado
às 12:06:23 local. O jogo chamou ListAutoLoad duas vezes e atingiu a criação
do save: encerrou estritamente com 90 em 128,313 s, NID 0x4dd03a4e,
cellSaveDataListAutoSave, LR 0x135bd70, thread 37. Esta é a próxima integração.
Capturas/logs e oráculo estão em private/analysis/trophy-installed-*.
Menu, gravação efetiva de save, partidas e progressão continuam não validados.


## Primeiro save original e callback de nove argumentos (2026-10-25)

Implementado cellSaveDataListAutoSave (NID 0x4dd03a4e) usando a seleção,
stat e loop de arquivos reais. O wrapper de contexto leva userdata de SP+112
até todos os callbacks, com retorno s32 estendido. Consulta de espaço livre
agora usa o volume real (e o ancestral existente antes de criar o diretório);
falhas não inventam capacidade. Root sem override acompanha PS3_HDD0_ROOT.
PARAM.SFO é escrito em temporário e renomeado; falhas de SFO propagam erro.
Stat informa o overhead de firmware de 35 KB e os tamanhos arredondados dos
arquivos reais. Limites: transação atômica do save inteiro e falhas durante
substituição de arquivos de dados ainda precisam ser implementadas/testadas.
A string de comunicação dos troféus passou a ter limite explícito de nove
bytes ao formar o caminho, sem usar o byte term como separador de diretório.

Dois testes novos reproduziram falta de HLE (90); depois passaram gravando e
relendo payload binário, PARAM.SFO e userdata atualizado, mais falha de root.
Sete testes de troféus, 41 de boot e 80 do projeto passaram; FullGame compilou.
Patch do SDK verificado também contra índice novo da revisão fixada, além
da aplicação idempotente. O probe aceita referência opcional do aviso de
autosave e envia Cross uma única vez após comparar pixels da região revisada.

list-auto-save (1792941536364536500) encerrou em 72,666 s com 90, após gravar
BLUS308820000A: ICON0.PNG 77414 bytes, PIC1.PNG 792086, SYS-DATA 2127971,
PARAM.SFO 2736 e metadados locais PARAM.PFD. Esse PFD é a representação local
do runtime, não um PFD criptográfico compatível com hardware PS3.
Os callbacks originais gravaram os bytes; não foi criado um perfil fictício.
Start e Cross foram autorizados pelos hashes de título e autosave, registrados
em private/analysis/list-auto-save-title-input.json. Próximo bloqueio:
spu-overlay-capacity, image 768455951, SPU 8195, PC 0x313c. O limite atual é
128 intervalos de ownership; investigar fragmentação/união, sem descartar
intervalos vivos ou permitir executar código sobrescrito. Leitura do save pelo
jogo após reinício ainda pendente, assim como menu, partida e progressão.


## Compactação de intervalos SPU e consulta do perfil após reinício (2026-10-25)

A fixture de 160 invalidações contíguas reproduziu spu-overlay-capacity com
90 no limite de 128 registros. Agora os intervalos são ordenados/compactados
entre as fases do DMA, sem reordenar a lista durante sua varredura. Tombstones
adjacentes se unem; código conhecido exige mesmo image_id, bias e continuidade
de origem. A fixture termina com dois intervalos: código válido executa e a
entrada sobrescrita permanece bloqueada. O limite não foi aumentado e registros
vivos não são descartados. Dumps de falha agora incluem o mapa de ownership.
42 testes de boot, 81 do projeto e 16 CTest do runtime passaram; FullGame compilou.

profile-reload (1792942053003372500) encerrou em 69,730 s com 90 antes de
retornar ao carregamento posterior: a listagem encontrou o perfil existente e
seu callback chamou cellSaveDataGetListItem (NID 0x04c06fc2), ainda ausente,
LR 0x135f260, thread 37. A leitura de SYS-DATA pelo jogo ainda não foi observada.
A remoção do bloqueio SPU no fluxo real também continua pendente dessa consulta.
README atualizado para remover afirmações antigas de ausência de gráficos/FIFAZF.


## Perfil original relido após reinício (2026-10-25)

Implementado cellSaveDataGetListItem, NID 0x04c06fc2, com nome, datas BE,
metadados do PARAM.SFO e soma real de tamanhos arredondados + 35 KB. Os outputs
são opcionais e só são escritos após validar arquivos e metadados. Saves ausentes,
nomes inválidos e SFO corrompido retornam erro mantendo buffers e arquivos.
O leitor de SFO deixa de aceitar silenciosamente metadados binários inválidos;
o formato textual antigo só é aceito se contiver o campo TITLE reconhecido.
Fixture consulta através do dispatcher real, compara datas com o host e prova
que arquivos não são alterados. Seis falhas antes do handler; depois quatro
testes de savedata, 42 de boot e 83 do projeto passaram; FullGame compilou.

Consulta isolada ao perfil real: FIFA Street / BLUS308820000A, 2964 KB.
metadata-reload (1792962560979039600, timeout 181,603 s) só conseguiu enviar
Start no final; a abertura mais lenta exigiu novo ensaio de 360 s.
metadata-reload-long (1792962788104760500) encerrou estritamente com 90 em
233,580 s. O jogo consultou o perfil e leu SYS-DATA em 524288 + 524288 +
524288 + 524288 + 30819 bytes, concluindo LOAD pelo callback original.
Hashes dos cinco arquivos continuaram iguais aos do primeiro save.
Isso valida gravação/releitura desse perfil, não toda progressão nem falhas
transacionais de saves completos. Menu e partida continuam pendentes.

O próximo bloqueio é spu-indirect em 0xb0, LR 0x3fbb4, SPU 8197. A inspeção
integral do blob identifica job_util_job_memcpy.elf, origem 0x1e63880, LS 0x80,
0x980 bytes, SHA da7145f8a13b2500457cc9de0b086d278037b4cbce75008be2468bed66a60c1f,
zero diferenças contra o residente. Não foi executado como se fosse o módulo
anterior naquele endereço; a entrada permanece estrita até tradução/revisão.


## Tarefa SPU original de cópia de memória (2026-10-25)

O blob job_util_job_memcpy.elf observado após o carregamento do perfil foi
traduzido como módulo AOT fixo: origem 0x1e63880, LS 0x80, 0x980 bytes,
SHA da7145f8a13b2500457cc9de0b086d278037b4cbce75008be2468bed66a60c1f.
A região de código termina em 0x8c0; as constantes seguintes não são admitidas
como instruções. A entrada 0xb0 preserva o CRT original. Seu desvio calculado
0x108 -> 0x134 foi conferido pelos valores de BSS 0xa00..0x1a80 e incluído
explicitamente no manifesto, junto ao destino 0x154 da limpeza desenrolada.

A fixture exclusiva de teste executa tanto a rotina 0x1d0 quanto o CRT 0xb0
pelo driver AOT real. Compara 18 tamanhos, de zero a 4097 bytes, em 16 pares
de alinhamentos, contra memcpy do host: 576 casos passaram, com origem e
guardas de destino preservadas. Mais 16 verificações confirmaram que a BSS
preenchida com sentinelas foi zerada na entrada original para cópia vazia.
O retorno é para um chamador autoral registrado somente nessa CLI de teste,
fora do módulo; não há substituição de callback nem de código no boot.
Erros iniciais da fixture (execução de apenas um fragmento e retorno sem
chamador) foram corrigidos no harness, sem alterar as instruções originais.
O probe de título ganhou --capture-start opcional; o padrão permanece 3001.


Ensaio nativo memcpy-native (1792964492801813900) terminou em 347,248 s com
90. O perfil foi novamente relido por inteiro; os hashes dos cinco arquivos
permaneceram iguais. A entrada job_util_memcpy foi observada na SPU 8196.
As 64 amostras de RefPack/DEFLATE conferiram com os oráculos independentes.
A captura antecipada enviou Start em frame_12, antes da janela de entrada
usada nos ensaios anteriores. O título continuou esperando; após revisão de
frame_33 e comparação de identidade da captura atual frame_37, uma segunda
pressão foi registrada em memcpy-native-start-retry.json. Não houve Cross
nem autorização automática de tela nova. O próximo bloqueio é spu-indirect,
PC 0x100, LR 0x3fbb4, SPU 8197: AssetStream_lzma.elf, origem 0x1e57180,
0x2000 bytes, SHA 6d5c19b1e71f7889531143ba08df360180077a8009b98cf4ddbbc1fdbaa21697.
O blob residente tem zero diferenças. Menu e partida continuam pendentes.

Validação final deste incremento: 42 testes de boot e 84 do projeto passaram;
FullGame com SPU compilou. O teste independente de cópia cobre 576 casos.


## Descompressão LZMA original: incremento em validação (2026-10-25)

O próximo módulo AssetStream_lzma.elf foi identificado por correspondência
integral de 8192 bytes com o snapshot de falha, origem 0x1e57180, LS 0x80,
entrada 0x100, código até 0x1d38. O CRT tem BSS 0x2080..0x20a0: seu salto
calculado entra em 0x19c; esse destino e 0x1a4 foram revisados e admitidos.
A tradução produziu 93 funções, sem instruções ou chamadas diretas pendentes.

A ABI observada é (output, capacidade, input, tamanho). A função em 0x530
constrói propriedades 5d 00 00 01 00, equivalentes a LZMA1 bruto, lc=3, lp=0,
pb=2, dicionário de 65536. O observador optativo captura até 32 jobs LZMA,
sem fornecer bytes ao jogo; o validador usa liblzma do Python com limite de
4 MiB e compara todos os bytes. Fluxos com tamanho conhecido podem omitir
marcador de fim; a igualdade com a saída capturada continua obrigatória.
Referências consultadas: docs.python.org/3.14/library/lzma.html e
https://raw.githubusercontent.com/ip7z/7zip/main/C/LzmaDec.h.

O novo runner de teste executou a entrada original 0x100 com 33 blocos
criados independentemente por liblzma: constantes, sequências e aleatórios,
11 tamanhos de 0 a 65672. Todos coincidiram com o conteúdo original, com
fonte preservada e guardas fora do span DMA arredondado em 16 bytes intactas.
A fixture não promete preservar os bytes de padding que o original escreve.
Antes da CLI/tradução houve 33 falhas; depois passou em 10,809 s.
O teste de aceitação do oráculo também falhou antes do suporte ao novo codec;
seis testes de oráculo passaram depois, incluindo corrupção e limite de expansão.


Validação final: FullGame compilou; 42 testes de boot e 87 do projeto passaram.
O oráculo também aceitou um bloco com saída completa sem marcador de fim.
Ensaio lzma-native (1792965360557405300) terminou com 90 em 276,841 s.
Start foi autorizado uma vez na captura frame_03 (frame de jogo 3361), sem
retry nem Cross. O perfil foi relido integralmente e seus cinco hashes foram
preservados. O job LZMA original executou na SPU 8197: 18451 bytes comprimidos
produziram 65672 bytes, todos iguais ao liblzma independente; SHA da saída
0c93a78cbd2eac4c390f13df48454b43876aece7f2d24d969925c00234dae07a.
As 65 amostras capturadas de assets passaram (32 RefPack, 32 DEFLATE, 1 LZMA).
O próximo bloqueio é sportsutil_dxt.elf: origem 0x1f8d580, LS 0x80, entrada
0xb0, 0x2250 bytes, SHA 3f1371daeeb5282209b1d95f45ae4f3608766b81cd009dffb32f98276c100604.
O snapshot tem zero diferenças contra o blob. Menu e gameplay ainda não validados.


## Compressão DXT original: incremento em validação (2026-10-25)

sportsutil_dxt.elf foi identificado integralmente no snapshot após LZMA:
origem 0x1f8d580, LS 0x80, 0x2250 bytes, SHA
3f1371daeeb5282209b1d95f45ae4f3608766b81cd009dffb32f98276c100604.
A tradução AOT tem 53 funções e nenhuma instrução/chamada direta pendente.
O código termina em 0x1ea8, antes das constantes. A BSS 0x22d0..0x23c0 faz
o CRT saltar a 0x118; o construtor indicado em 0x22c0 aponta para 0x3e0.
Esses destinos foram conferidos explicitamente. As rotinas 0x3f0 e 0xa80
recebem saída LS, pixels ARGB LS, pitches de origem/destino, largura e altura.
Elas são compressores de blocos; o nome DXT sozinho não foi tratado como
prova de descompressão. O job principal usa fila/atomics e será validado no boot.

A fixture de teste executa o construtor original e ambas as rotinas em
imagens autorais com pitch maior que a largura útil. O decoder independente
segue o layout BC1/BC3 de Microsoft Learn (mesma referência em test_spu_dxt.py).
A comparação usa blocos de cor uniforme para não exigir uma escolha particular
de endpoints de um compressor com perdas. Limites declarados: até 9 unidades
por componente RGB por quantização e 1 de alpha em BC3. A origem, guardas e
padding entre linhas devem permanecer intactos. São 48 combinações de formato,
dimensão e rotação da paleta, incluindo primárias e valores distintos de alpha.
Antes da nova CLI/tradução, as 48 combinações falharam por CLI inexistente.


Validação: 48 casos dos compressores passaram em 7,871 s. O decoder foi
conferido separadamente com endpoints/índices conhecidos, transparência BC1 e
as duas tabelas de alpha BC3. FullGame compilou; 42 testes de boot e 89 do
projeto passaram. O ensaio dxt-native (1792966178932428000) terminou com 90
em 275,578 s. O título autorizou Start em frame_02 e o aviso de autosave
revisado autorizou Cross em frame_03. O perfil foi novamente relido inteiro.
As 65 amostras RefPack/DEFLATE/LZMA coincidiram com os oráculos.
A entrada sportsutil_dxt foi observada na SPU 8197. Outra SPU, 8196, atingiu
um novo módulo dxt_encoder_job.elf: origem 0x2018e80, LS 0x80, 0x4900 bytes,
SHA d1cd200c70dd379efd997680333a35b7c1a16b7d5fdd0c3791ba69193b4824c0,
zero diferenças contra o residente. O processo parou ali; a entrada do job
sportsutil foi confirmada, mas não a conclusão de toda sua fila concorrente.
Menu navegável, cena e partida continuam sem validação.


## Segundo encoder DXT e descritor de trabalho (2026-10-25)

Módulo dxt_encoder_job.elf identificado no snapshot: origem 0x2018e80,
LS 0x80, 0x4900 bytes, SHA d1cd200c70dd379efd997680333a35b7c1a16b7d5fdd0c3791ba69193b4824c0.
O código termina em 0x4820, antes da tabela de índices/constantes; a BSS é
0x4980..0x4a00. O destino calculado do CRT é 0x134. Não há construtores
na tabela vazia 0x4960. A tradução gerou 243 funções, sem instruções nem
chamadas diretas pendentes. A nova fixture roda a entrada 0xb0 inteira.
O descritor autoral tem 48 bytes, com contador e acumulador de custo de erro,
endereços de origem/destino, largura, formato, pitches e número de faixas
com quatro linhas. O oráculo existente de BC1/BC3 foi reaproveitado.
Antes da nova CLI/tradução, as 48 combinações adicionais falharam por CLI
inexistente. A validação deve conferir cores, guardas, padding, origem,
campos imutáveis e atualização dos dois contadores ao retornar ao chamador.


A primeira expectativa da fixture estava errada: +4 acumula custo de erro,
não bytes escritos. A falha em preto mostrou resultado 0, origem intacta e
somente +7 diferente (esperado 8, observado 0). A revisão de 0x1e40 confirmou
o retorno zero do caminho de blocos uniformes. A fixture agora inicia esse
campo com 37 e verifica que +=0 o preserva, sem exigir contagem de bytes falsa.
Outro diagnóstico confirmou BC1 com transparência de 1 bit (alpha <128):
blocos vermelhos com alpha 0/1/64/127 viram transparentes; 128/254/255 ficam
opacos. As cores dos texels transparentes não são comparadas como se fossem
visíveis. Por fim, formato 0x100 produziu alpha explícito de 4 bits (0/44/88/ff
repetidos nos bytes dos blocos), identificando BC2. A fixture BC3 foi corrigida
para 0x200, sem relaxar sua tolerância de alpha. Não houve mudança nas
instruções traduzidas nem no runtime para fazer esses testes passarem.
Os três testes DXT passaram em 11,797 s: referências do decoder, 48 casos
das rotinas sportsutil e mais 48 casos do job completo. O contador de trabalho
terminou em faixas+1; origem, campos imutáveis, guardas e padding permaneceram
intactos. A soma de custos de blocos não uniformes e execução de múltiplos
workers sobre o mesmo descritor ainda não foram validadas por essa fixture.


Validação do incremento: FullGame compilou, 42 testes de boot e 90 testes
do projeto passaram. O patch versionado continua idêntico ao diff do SDK.
O ensaio dxt-encoder-native (1792967392239208200) terminou por timeout em
481,377 s, sem falha estrita e sem alcançar o novo encoder: a referência
exata do texto PRESS START pulsante não coincidiu com os pixels capturados.
O título foi visto em frame_18, frame_26 e frame_50; title_not_seen no relatório
é o estado do reconhecedor, não ausência de renderização. Um Start manual foi
registrado após revisar o attract movie; as outras tentativas manuais não
escreveram input porque a captura atual já havia mudado. Nenhum resultado
desse ensaio foi contado como validação da entrada do novo módulo.
A repetição usa novamente o título estável e os parâmetros dos ensaios anteriores.


A repetição dxt-encoder-baseline-gate (1792967895702785400) foi interrompida
externamente antes de relatório/timeout: stderr terminou em 22:40:15 UTC,
com 2220 flips, sem fifa-block; os processos e a sessão do terminal já não
existiam ao verificar. A causa não foi demonstrada e isso não é tratado como
falha do jogo. O runner seguinte foi iniciado com Start-Process oculto, em
processo separado da sessão do terminal, e acompanhado até a saída efetiva.

Ensaio dxt-encoder-detached (1792968259784429900): 90 em 307,650 s. Start foi
autorizado em frame_04 pelo título estável. O aviso de autosave teve glifos
corrompidos, antes de alcançar o novo encoder. A referência visual e os 71
draws do manifesto coincidiram, normalizando somente frame_count e endereços
de shader/texturas (preservando formatos, remaps, dimensões e contagens).
Cross manual foi registrado em dxt-encoder-detached-manual-cross.json; não se
relaxou o reconhecedor automático. O código original releu SYS-DATA inteiro.
Os cinco hashes do perfil foram preservados e 65 amostras de assets passaram.
As entradas sportsutil_dxt e dxt_encoder_job foram observadas, respectivamente
nas SPUs 8196 e 8197. Outra SPU, 8194, parou na entrada 0xb0 de
aififa_topologycache_spu.elf, origem 0x1ebd580, 0xdb40 bytes, SHA
06cb06e15272bef85f694bb916226be58677518355088bb38c2d55ddbfa254b7.
O snapshot tem zero diferenças. Isso confirma a entrada dos encoders no jogo;
não comprova o processamento completo de todas as filas concorrentes.
Menu e partida continuam pendentes. A corrupção intermitente das fontes e
os artefatos do vídeo de abertura também precisam de correção/validação.


## Invalidação do cache de texturas e glifos (2026-10-25)

A captura dxt-encoder-detached/frame_38 tinha o aviso de autosave com glifos
corrompidos; a referência trophy-installed/frame_10 tinha o mesmo aviso legível.
A/B sem mudar o executável: TEX_NOCACHE=1 no ensaio font-cache-full-upload
(1792968876477761500) restaurou exatamente os pixels da região revisada.
O probe enviou Start e Cross automaticamente e o processo chegou ao bloqueio
conhecido da topologia em 82,356 s, com saída 90. Isso localizou a falha no
caminho do cache; o reenvio forçado foi diagnóstico, não solução de entrega.

O checksum antigo lê só 4 bytes a cada 128 em um atlas B8 de 512x256.
Uma alteração autoral de 320 bytes (glifo 16x20 em x=40,y=20) preservou
521235909 no checksum, embora SHA256 dos bytes fosse diferente. A fixture
reproduz esse ponto cego e exige detecção do glifo e de 63 mutações em início,
meio e final de blocos de 1..131075 bytes, com leituras desalinhadas e tails.
A nova impressão de conteúdo de 64 bits lê todos os bytes em palavras via
memcpy e processa a cauda. É interna ao processo, sem formato persistido.

O backend passa a registrar a impressão ANTES de converter pixels, evitando
marcar dados escritos depois da leitura como se já tivessem sido enviados.
Permanece o reuso quando os bytes não mudam; TEX_NOCACHE não é ativado como
padrão. O helper está no patch do SDK, não solto em vendor. O patch passou
em índice isolado da revisão original. 42 testes de boot, 91 do projeto e
16 CTest do runtime passaram; FullGame compilou. Ainda é preciso conferir o
aviso no cache normal após a correção. Coerência de outros níveis de mipmap,
faces de cubo e atualizações dentro do mesmo frame não é provada por esse teste.


Validação nativa com cache normal: font-cache-fixed
(1792969354888225400), saída 90 em 140,128 s. TEX_NOCACHE não foi herdado
pelo processo. A região de texto do aviso em frame_05 coincidiu exatamente
com a referência (SHA 4ab853e27bb6238ca6188b7bd11529fe18f50f60aa494f769d0202598e9fe7ec),
foi conferida visualmente e o probe autorizou Cross automaticamente.
O perfil foi relido inteiro e os cinco hashes foram preservados; 65 amostras
de assets coincidiram. O próximo blob continuou sendo aififa_topologycache_spu,
confirmado por SHA integral do snapshot. A correção dos glifos vale para essa
cena revisada; menu, partida, fidelidade geral e desempenho seguem pendentes.


## Inicialização original do módulo de topologia (2026-10-25)

Integrado no manifesto o blob aififa_topologycache_spu.elf, origem 0x1ebd580,
LS 0x80, 0xdb40 bytes, SHA 06cb06e15272bef85f694bb916226be58677518355088bb38c2d55ddbfa254b7.
O código termina em 0xd360, antes das constantes; a BSS é 0xdbc0..0xfdf0.
O CRT salta a 0x148 ao iniciar a limpeza parcial de 0x30 bytes. Os sete
ponteiros da tabela 0xdb50..0xdb68 foram conferidos: 0xdc8, 0x68b8, 0x7a50,
0x7db8, 0xa128, 0xcfd0 e 0xd090. A sequência real percorre a tabela ao contrário.
Esses destinos e 0x154 foram admitidos explicitamente, sem interpretar código.
A tradução gerou 604 entradas, sem instruções ou chamadas diretas pendentes.

A fixture exclusiva de teste carrega o blob e executa os sete construtores
originais em ordem do CRT, com BSS zerada na preparação do contexto e retorno
para um chamador autoral fora do módulo. Os sete retornaram e a comparação
confirmou que cabeçalho/código não foram modificados. Não há substituição do
main nem validação de algoritmo de IA por esse teste. Antes da CLI/tradução o
teste falhou; depois passou em 3,066 s. FullGame compilou. A entrada do módulo
no boot e o processamento dos dados reais continuam sendo o próximo aceite.


Validação do incremento: FullGame compilou, 42 testes de boot e 92 do projeto
passaram. Ensaio topology-native (1792981780866319400): 90 em 102,270 s.
Start e Cross foram autorizados pelos pixels do título e do aviso legível;
o perfil foi relido integralmente, com os cinco hashes preservados. As 65
amostras de assets conferiram. A entrada aififa_topologycache foi observada
na SPU 8192. Outra SPU, 8194, atingiu o próximo módulo não traduzido:
railtracks_movetotarget_spu.elf, origem 0x2034680, LS 0x80, 0x2a6a0 bytes,
SHA f0d60bc73fa56d84a06dc6085e2308b6d502a416d5b27a7997fb76d2bb62cf8b,
zero diferenças contra o snapshot. A entrada de topologia está confirmada;
não se afirma conclusão de todas as tarefas/algoritmos concorrentes.
Menu e partida continuam pendentes.


## Módulo railtracks_movetotarget em integração (2026-10-25)

Blob identificado integralmente: origem 0x2034680, LS 0x80, 0x2a6a0 bytes,
SHA f0d60bc73fa56d84a06dc6085e2308b6d502a416d5b27a7997fb76d2bb62cf8b.
A análise não usou o último bi r0 como fim do código: há retornos condicionais
e rotinas de saída depois de 0x28f58. O limite revisado é 0x29080, antes das
constantes. A BSS é 0x2a720..0x2f770 e o salto calculado do CRT entra em 0x140.
A tabela 0x2a6a0..0x2a6ac contém quatro construtores: 0x1d390, 0x1edb0,
0x24a38, 0x26868; a execução percorre a ordem inversa. Destinos explícitos
no manifesto preservam a entrada original e a checagem estrita.
A tradução gerou 1571 entradas, sem instruções nem chamadas diretas pendentes.

O runner de construtores foi reaproveitado, preservando a CLI de topologia,
e ganhou uma CLI separada para Railtracks. O teste novo falhou antes da nova
CLI/tradução; os construtores anteriores continuaram passando. O aceite do
novo teste é retornar dos quatro construtores sem modificar cabeçalho/código;
isso não valida o algoritmo de movimentação nem substitui o main do jogo.


Validação: FullGame compilou; quatro construtores de Railtracks e sete de
topologia passaram, preservando código. 42 testes de boot e 93 do projeto
passaram. Ensaio railtracks-native (1792982437186954100): entrada original
observada na SPU 8194, após Start/Cross autorizados pelas capturas legíveis.
Perfil relido inteiro e cinco hashes preservados; 65 amostras de assets passaram.
O próximo bloqueio é uma segunda versão ANT_kernel.elf, origem 0x2030080,
LS 0x80, entrada 0x180, 0x45c0 bytes, SHA
18664f851235de1b95b6fc827b73bfc18b9714425043fdcbf416a029373a94e4.
Dois snapshots completos conferiram integralmente; outro JSON ficou vazio
quando o processo terminou durante falhas concorrentes.

Uma linha fifa-spu-state truncada fez o parser do runner abortar depois da
execução. O código de saída e o tempo final não foram persistidos e permanecem
null, sem inferir 90 como medição do processo. Foram recuperados do log bruto
139 eventos válidos, o fifa-block completo e os oráculos de assets, com um
erro de parsing registrado em railtracks-recovered.json. A próxima correção
preservará o status do processo antes do parsing e registrará linhas inválidas.
Não se afirma resultado do algoritmo de movimentação nem menu/partida funcional.


## Relatório preservado após diagnóstico truncado (2026-10-25)

A falha concorrente de ANT interrompeu uma linha fifa-spu-state em image=526,
mas o fifa-block e outros 138 eventos estavam íntegros. O runner agora grava
process-exit.json imediatamente após wait/cleanup, antes de analisar eventos ou
assets. O parser mantém os objetos JSON completos e registra linha, tipo, erro
e amostra bruta de até 4096 caracteres para entradas inválidas; elas não viram
eventos inventados nem descartam o resto do relatório. Payloads que não sejam
objetos também são registrados como erro. O tempo medido passa a terminar na
saída do processo, excluindo o pós-processamento dos logs/oráculos.

Três testes reproduziram o problema antes da correção. Depois passaram:
linhas truncadas/tipos inválidos preservam eventos seguintes; relatório retém
saída 90; status já está salvo mesmo se o parser falhar depois. O processo dos
testes é um mock explícito em diretório temporário, não uma validação do jogo.
O parser novo leu o log real: 139 eventos íntegros e um erro registrado.
O status perdido do ensaio antigo não foi retroativamente inventado.

Validação final do runner: 96 testes do projeto passaram.


## Segunda versão do kernel ANT (2026-10-25)

O snapshot de 0x180 contém ANT_kernel.elf de 0x2030080, não o binário de
0x201d880 já traduzido. O novo blob tem 0x45c0 bytes, SHA
18664f851235de1b95b6fc827b73bfc18b9714425043fdcbf416a029373a94e4,
entrada 0x180 e código até 0x4130. A cauda após o último bi r0 contém uma
rotina que termina em br 0x3d98; esse trecho foi preservado como código.
A BSS 0x4640..0x4870 faz o CRT entrar em 0x218; 0x224 e os construtores
0x1de8/0x40b8 foram conferidos e admitidos explicitamente. A tabela original
em 0x4240/0x4244 é percorrida em ordem inversa.

A tradução produziu 305 entradas, sem instruções nem chamadas diretas pendentes.
O teste novo reproduziu CLI ausente; depois os dois construtores retornaram
com código preservado. Os três testes de construtores passaram em 3,853 s
(topologia, Railtracks e ANT secundário). FullGame compilou. O mapa real de
ownership mostrou o kernel novo ocupando o prefixo LS e código de Railtracks
residente acima de 0x4670; não se reutilizou código do ANT antigo só pelo nome.
A execução no carregamento real foi observada no ensaio abaixo; callbacks e
conclusão de todas as tarefas ainda não estão validados.


Validação nativa ant-secondary-native (1792983860434703700): saída estrita 90
medida aos 81,795 s e entrada ant_kernel_secondary observada na SPU 8194.
Start/Cross foram autorizados pelos mesmos ROIs conferidos; a captura posterior
mostra carregamento, sem menu. Os cinco hashes do perfil foram preservados.
O parser novo conservou o relatório mesmo com uma linha fifa-spu-state truncada;
process-exit.json já estava salvo. O próximo PC 0x4940 está em um plugin ANT
PIC, origem 0x2100a00, LS 0x4910, tamanho 0x71e0, SHA
e10fdf3acb9f374397a13bd37f843cf866891f8c7432a5fb9b545b3a13af65d2;
o blob desse snapshot confere integralmente. Outros workers param em 0x4920.
42 testes de boot e 97 do projeto passaram. Não se afirma conclusão das tarefas
ANT, menu ou gameplay; o próximo incremento examinará o plugin e suas relocações.


## Dois plugins ANT relocáveis após o kernel (2026-10-26)

O ensaio do kernel secundário revelou módulos diferentes em workers concorrentes:
- vbrcodec_clipnode.elf: origem 0x2100a00, 0x71e0 bytes, LS observado 0x4910;
  SHA e10fdf3acb9f374397a13bd37f843cf866891f8c7432a5fb9b545b3a13af65d2.
- defaultposenode_dofset.elf: origem 0x210b300, 0x1610 bytes, LS 0x48f0;
  SHA d4ab78e9f9c3c0fc453b18fb06cdbadd47481cec4e9a4d0da6c0ffb36b1f2504.

Os três snapshots conferem integralmente os respectivos plugins. Cabeçalhos
PIC declaram flag 0x80000000, modo 1 e entrada relativa 0x30. A tradução usa
base canônica zero com deslocamento de ownership já existente, preservando
memória absoluta do kernel e referências relativas do plugin. Não se criam
variantes fixas por endereço nem se reutiliza código diferente só pelo nome.

Em VBR, código termina em 0x62a0: a última rotina em 0x6290 termina com branch
para 0x5fd8; em pose, código termina em 0x10f8, antes do padding/tabela 0x1100.
As tabelas de três construtores ficam em 0x62a0 e 0x1100, percorridas para frente
pelo CRT, ao contrário do CRT dos módulos anteriores. BSS tem 0x50 bytes em ambos.

Dois testes novos falharam por CLI ausente antes da integração. O fixture novo
executa os três construtores originais, com fonte conferida/ownership PIC, nas
bases 0, 0x48f0, 0x4910 e 0x10000. Confere preservação de código, guardas de dados
e consistência dos dados finais entre posições, permitindo somente diferenças
de ponteiros que somam a base. Exige haver ponteiros efetivamente relocados.
Isso cobre inicialização estática, não o algoritmo de animação nem o main completo.
A tradução gerou 279 entradas VBR e 75 de pose, sem instruções ou chamadas
diretas pendentes. Os cinco testes de construtores passaram (24 execuções dos
novos construtores nas quatro bases, além dos módulos anteriores), em 4,292 s.
O primeiro fixture falhou nas guardas porque usava sizeof do ponteiro LS ao
preencher a memória; a correção usa SPU_LS_SIZE. Não houve ajuste no código
original nem relaxamento das guardas para obter aprovação. FullGame compilou;
boot passou seus 42 testes e os 99 testes do projeto passaram em 7,662 s.
O ensaio ant-plugins-native foi concluído conforme registrado abaixo.


Ensaio ant-plugins-native (1792984404123856500): saída estrita 90 aos 80,660 s.
Entrada de defaultposenode_dofset observada em LS 0x48f0; a entrada VBR não foi
observada. Nova parada spu-overlay-layout em LS 0x3d300 durante leitura de apenas
64 bytes do cabeçalho VBR, feita pelo kernel em PC 0x99c, com r8=0x40.
O runtime tentava admitir o span inteiro (0x71e0), que ultrapassaria a LS a partir
da pilha. Essa leitura de metadados não demonstra tentativa de executar ali.
Outro worker também relatou PC ausente 0x5fd0; seu JSON foi interrompido e
permanece preservado. O próximo incremento separará leitura parcial e admissão
executável com teste de regressão. 65 amostras de assets passaram; cinco hashes
do perfil preservados. Menu e partida continuam pendentes.


## Cabeçalhos PIC na pilha sem ownership executável (2026-10-26)

O kernel lê 64 bytes de 0x2100a00 em LS 0x3d300 durante inspeção de metadados;
o blob completo tem 0x71e0 bytes e não caberia nessa posição. O runtime conferia
o hash da fonte e depois rejeitava o layout inteiro, apesar da leitura limitada
ser válida. Agora uma cópia parcial alinhada, contida na LS, de fonte PIC válida,
é mantida como dados quando somente o span inteiro ultrapassaria a LS.
Os bytes efetivamente copiados recebem tombstone, impedindo fallback para uma
função antiga no mesmo endereço. Não há admissão executável do restante do módulo.
O comportamento das demais admissões parciais não foi redesenhado neste incremento.

O fixture reproduz uma leitura de 64 bytes no fim da LS, verifica dados intactos,
nega lookup mesmo com entrada antiga registrada e depois executa uma imagem
completa em posição válida. Outros caminhos tentam executar os metadados (64 ou
16 bytes) e continuam terminando com spu-indirect/90. Fonte alterada, flag
absoluta e carga completa desalinhada continuam bloqueadas. Os três caminhos
novos falharam antes da correção. O patch do SDK permanece versionado e passou
apply --cached --check em índice isolado da revisão fixada. Boot: 43 testes;
runtime: 16 CTest. FullGame compilou e os 100 testes do projeto passaram
em 14,830 s. O ensaio real deste ajuste será registrado no próximo checkpoint.


## Plugin clearactivitymasknode_exec (2026-10-26)

O stderr de ant-plugins-native registrou PC 0x5fd0 em outro worker. Embora seu
JSON tenha ficado vazio, o arquivo .ls de 262144 bytes foi persistido. Em LS
0x5fa0 há um cabeçalho original que corresponde unicamente ao ELF em 0x20bba00;
os 0xad0 bytes conferem integralmente, SHA
5ebd1592be5f06df6d2176da36b700bb75511693b853b3051ac16332d8f685ba.
O nome completo após BuiltElfName é clearactivitymasknode_exec.elf. Essa análise
usa bytes do LS e PC do log, sem preencher o JSON original incompleto.

Cabeçalho PIC modo 1, entrada 0x30, BSS 0xad0..0xb20. Código termina em 0x6c8:
a rotina 0x6b8 termina com branch 0x3f8; a tabela começa em 0x6d0 e contém
0x330, 0x3f0, 0x6b8 na ordem percorrida pelo CRT. O teste usa os construtores
originais em quatro bases, incluindo a posição real 0x5fa0, com as mesmas
checagens de código, guardas e dados relocados. A CLI ausente retornou 2 antes
da integração. A tradução gerou 38 entradas, sem instruções ou chamadas diretas
pendentes. FullGame compilou; seis testes de construtores passaram em 5,494 s.
43 testes de boot e 101 do projeto passaram. O ensaio ant-clear-native verifica
a entrada real; ant-header-native usou somente a correção de metadados anterior.


Ensaio ant-header-native (1792984939460393700): saída estrita 90 aos 82,530 s,
sem spu-overlay-layout. O carregamento passa da inspeção de cabeçalho e para
no PC 0x5fd0 do clearactivitymasknode_exec. Foram preservados os cinco hashes
do perfil e passaram 65 amostras de assets. Não houve entrada VBR registrada
antes da parada concorrente; isso permanece pendente. A correção de metadados
foi exercitada no carregamento real sem retirar a checagem de execução ausente.


Ensaio ant-clear-native (1792985246954273600): saída estrita 90 aos 95,523 s.
VBR entrou na SPU 8192, e clearactivitymasknode_exec na 8193. O próximo módulo
PIC aparece em LS 0x6b10, PC 0x6b40, origem 0x2118680, tamanho 0x1710;
dois snapshots completos conferem integralmente seus bytes. Os cinco hashes
do perfil permanecem preservados e 65 amostras de assets passaram. Uma linha
SPU truncada foi registrada sem perda do status/relatório. Menu e partida ainda
não foram alcançados. Próxima ação: conferir e traduzir o módulo de 0x2118680.


## Plugin setdofsetnode_exec (2026-10-26)

Dois snapshots completos do ensaio ant-clear-native identificaram o mesmo plugin
em LS 0x6b10, PC 0x6b40: origem 0x2118680, 0x1710 bytes, SHA
c7c203e58e7e0005165cd965445d4c56aa2d07aecc9e3ac31d2bacfa9dcd858f,
sem diferença nos bytes. BuiltElfName registra setdofsetnode_exec.elf.
Cabeçalho PIC modo 1 e entrada relativa 0x30. O código termina em 0x11f8,
seguido por padding de oito bytes e tabela de construtores em 0x1200.
A rotina final 0x11e8 termina com branch 0xf30; esse trecho foi preservado.
BSS 0x1710..0x1760; construtores 0xe60, 0xf20 e 0x11e8, percorridos para frente.

O fixture usa as bases 0, 0x6b10, 0x4910 e 0x10000. A CLI ausente retornou 2
antes da integração. A tradução produziu 83 entradas, sem instruções nem
chamadas diretas pendentes. FullGame compilou; sete testes de construtores
passaram em 6,621 s. Boot passou os 43 testes e os 102 testes do projeto
passaram em 8,430 s. O ensaio ant-setdof-native segue em validação. Não se
afirma resultado completo do processamento de animação.


Ensaio ant-setdof-native (1792985700118448800): saída estrita 90 aos 106,490 s.
Entrada de setdofsetnode_exec observada na SPU 8194. Dois próximos plugins:
0x20e2f00 em LS 0xbb90/PC 0xbbc0 (0x19e0 bytes) e 0x20be100 em LS
0x82c0/PC 0x82f0 (0xfe0 bytes). Os snapshots completos conferem os blobs
inteiros. Cinco hashes do perfil preservados; 65 amostras de assets passaram.
Ainda não há menu/partida validado. Próximo incremento: conferir e integrar
os dois módulos alcançados, sem trocar os seus callbacks por implementações falsas.


## Delta trajectory e scratch memory clear (2026-10-26)

O ensaio setdof revelou dois plugins distintos em workers concorrentes:
- deltatrajectoryplugin.elf, origem 0x20e2f00, 0x19e0 bytes, LS 0xbb90,
  SHA f0eed6604a62a7f6fc8745b17cd79ebf53f2556c1ece802da7e0c80d0ca1afa6.
- scratchmemclear_exec.elf, origem 0x20be100, 0xfe0 bytes, LS 0x82c0,
  SHA 86b9892f5273873cac6129197232cde4c34474992d3ee34d3981aa673e7ef36d.

Bytes completos dos novos módulos conferidos nos snapshots. Ambos declaram
PIC modo 1, entrada 0x30 e BSS de 0x50 bytes. Em trajectory, código termina em
0x11d8: rotina 0x11c8 termina com branch 0xf10, antes de padding e tabela
0x11e0; construtores 0x888/0xf00/0x11c8. Em scratch, código termina em 0xbd8:
rotina 0xbc8 termina com branch 0x910, antes da tabela em 0xbe0;
construtores 0x840/0x900/0xbc8. A ordem dos construtores é para frente.

As duas CLIs ausentes retornaram 2 antes da integração. Cada teste usa quatro
bases, incluindo a respectiva posição observada, e confere código, guardas e
dados relocados. FullGame compilou; nove testes de construtores passaram em
4,218 s. Boot passou seus 43 testes e 104 testes do projeto passaram em 8,481 s.
O ensaio ant-trajectory-scratch-native segue em validação. A última captura
do ensaio setdof foi inspecionada: continua na imagem original de carregamento,
sem menu navegável. Não há conclusão validada dos algoritmos de animação.


Ensaio ant-trajectory-scratch-native (1792986197997724500): saída estrita 90 aos
88,383 s. Entrada de trajectory observada na SPU 8193 e scratch na 8192.
VBR também entrou em outra posição, LS 0x9340 na SPU 8194, sem criar variante
fixa adicional. Próximos módulos: 0x20e6e80 em LS 0xd610/PC 0xd640,
0x1b90 bytes; e 0x210ca00 em LS 0x105c0/PC 0x105f0, 0x1580 bytes.
Ambos conferem integralmente nos snapshots completos. Perfil preservado pelos
cinco hashes e 65 amostras de assets aprovadas. O tempo final medido não confirma
regressão de desempenho. Menu, partida e resultados completos de animação
seguem pendentes. Próximo incremento: os dois módulos efetivamente alcançados.


## Pose to global e set DOF node (2026-10-26)

O ensaio trajectory/scratch alcançou dois plugins adicionais:
- posetoglobalplugin.elf: 0x20e6e80, 0x1b90 bytes, LS 0xd610, SHA
  1e8f997d11c7d9f333236c9381ea8ad1145a275e31b470c40b870584bce15b2d.
- setdofnode_exec.elf: 0x210ca00, 0x1580 bytes, LS 0x105c0, SHA
  c83ad4290fd1d28dfa254ddb69ccca36bda3df8a8216fda318591dee82114cdf.

Os dois blobs completos conferem nos snapshots. Cabeçalhos PIC modo 1,
entrada relativa 0x30 e BSS de 0x50 bytes. Global pose: código até 0x1678,
rotina final 0x1668 terminando com branch 0x13b0; padding até a tabela 0x1680,
construtores 0x1248/0x13a0/0x1668. Single DOF: código até 0x1070, rotina
final 0x1060 terminando com branch 0xda8; a tabela começa imediatamente em
0x1070, com 0xcd8/0xd98/0x1060. Ambos percorrem os construtores para frente.

As CLIs ausentes retornaram 2 antes da integração. Testes novos incluem a
posição observada de cada plugin, além de 0, 0x4910 e 0x10000, preservando as
checagens de código/guardas e consistência de dados relocados. A tradução gerou
74 entradas por módulo, sem instruções nem chamadas diretas pendentes. FullGame
compilou; os 11 testes de construtores passaram em 9,968 s. Boot passou seus
43 testes, e 106 testes do projeto passaram em 9,344 s. O ensaio
ant-globalpose-singledof-native segue em validação; não se afirma animação completa.


Ensaio ant-globalpose-singledof-native (1792986607398190400): saída estrita 90
aos 82,973 s. Entradas de posetoglobalplugin (SPU 8193) e setdofnode_exec
(SPU 8192) observadas. Próximo plugin em LS 0x11be0/PC 0x11c10, origem
0x20bd280, 0xd70 bytes, integralmente conferido em dois snapshots completos.
Os cinco hashes do perfil permanecem iguais e 65 amostras de assets passaram.
Menu, partida e resultado completo dos algoritmos de animação seguem pendentes.
Próximo incremento: examinar e traduzir o módulo de 0x20bd280.


## Plugin groupnode_combine_exec (2026-10-26)

Dois snapshots completos de globalpose/singledof apontam o mesmo plugin em
LS 0x11be0/PC 0x11c10: origem 0x20bd280, 0xd70 bytes, SHA
5b33018d3516f1633158aa79ca7c90f2e5d2f70b704ebdf4bd6f76f7a773054e,
sem diferença nos bytes. BuiltElfName registra groupnode_combine_exec.elf.
Cabeçalho PIC modo 1, entrada 0x30 e BSS 0xd70..0xdc0. Código até 0x968,
com rotina final 0x958 terminando em branch 0x6a0; padding até a tabela
0x970. Construtores 0x5d0/0x690/0x958, percorridos para frente.

A CLI ausente retornou 2 antes da integração. O fixture testa quatro bases,
incluindo 0x11be0, com checagem de código, guardas e dados relocados.
A tradução gerou 57 entradas, sem instruções nem chamadas diretas pendentes.
FullGame compilou; os 12 testes de construtores passaram em 4,476 s. Boot passou
43 testes e os 107 testes do projeto passaram em 7,923 s. O ensaio
ant-groupcombine-native segue em validação. Não se afirma conclusão do algoritmo
de combinação de animação nem gameplay validado.


Ensaio ant-groupcombine-native (1792986961606971500): saída estrita 90 aos
81,132 s. Entrada groupnode_combine_exec observada na SPU 8192, LS 0x11be0.
O próximo módulo já substitui a região inicial em LS 0x48f0, PC 0x4920,
origem 0x20e8c80, 0x6af0 bytes. Dois snapshots completos conferem os bytes
inteiros do módulo novo; ele não deve usar a tradução do antigo dono de 0x48f0.
Perfil preservado pelos cinco hashes e 65 amostras de assets aprovadas.
Não houve menu ou gameplay validado. Próximo incremento: módulo de 0x20e8c80.


## Plugin DCT de clipes ANT (2026-10-26)

Os snapshots do ensaio groupcombine conferem integralmente dctcodec_clipnode.elf
em LS 0x48f0/PC 0x4920: origem 0x20e8c80, 0x6af0 bytes, SHA
606fcdb43d4b7692d5cf3a19dbad7dc52b75da52d4e4f73b016504847fb80c8f.
Essa região substitui módulos anteriores; o código admitido é o deste hash.
Cabeçalho PIC modo 1, entrada 0x30, BSS 0x6af0..0x6b40. Código termina em
0x6040, imediatamente antes da tabela de construtores. A rotina final 0x6030
termina com branch 0x5d78. Construtores 0x4ff8/0x5d68/0x6030, em ordem para frente.

A CLI ausente retornou 2 antes da integração. O teste usa as bases 0, 0x48f0,
0x4910 e 0x10000, com código/guardas preservados e dados relocados consistentes.
A tradução produziu 252 entradas, sem instruções nem chamadas diretas
pendentes. FullGame compilou e os 13 testes de construtores passaram em 7,562 s.
Boot passou os 43 testes e 108 testes do projeto passaram em 8,257 s. O ensaio
ant-dct-native segue em validação. Testar construtores não valida integralmente
a decodificação DCT de animação.


Ensaio ant-dct-native (1792987320028365500): saída estrita 90 aos 80,563 s.
DCT entrou na SPU 8194, LS 0x48f0. O próximo plugin é groupnode_final_exec.elf,
origem 0x20bc580, LS 0xb480/PC 0xb4b0, 0xc60 bytes, conferidos integralmente
em dois snapshots completos. Cinco hashes do perfil preservados; 65 amostras
de assets aprovadas. Menu e gameplay continuam pendentes.

Um levantamento privado de cabeçalhos com quatro ila r2 e marcador/tamanho
coerentes encontrou 157 programas raw no ELF. Isso não implica tradução nem
cobertura completa do inventário. Há uma família numerosa de plugins ANT com
CRT equivalente; o próximo incremento preparará revisão estrutural e testes
em lote, mantendo limites explícitos, hashes e parada estrita de execução.


## Inventário raw e revisão estrutural da família ANT (2026-10-26)

A ferramenta tools/inventory_spu_raw.py valida o hash do ELF, segmentos PT_LOAD,
alinhamento, quatro ila r2, marcador BuiltElfName, tamanho e nome terminado em
NUL dentro de limite. reports/spu-raw-inventory.json registra 157 imagens raw
reconhecidas, sem afirmar inventário exaustivo e sem incluir bytes do jogo.

O revisor compara o CRT com o VBR original já conferido e de hash fixado, permitindo
variação somente nas construções de endereço de BSS/tabela e chamada de main.
Confere registradores/opcodes, limites de BSS, três construtores alinhados em
ordem, terminador, cauda final il/ila/br/lnop, destino dentro do código e zero
no padding de oito bytes quando presente. O limite final vem da cauda revisada,
não de procurar o último bi ou de classificar todos os bytes como instruções.
A ferramenta não altera o manifesto nem admite código automaticamente.

49 plugins de antcommonplugins satisfazem essa revisão. Predictable blend e
mirror não correspondem ao perfil de cabeçalho e exigem análise separada.
O próximo incremento acrescentará os 39 ainda não integrados e executará seus
construtores em quatro bases. Isso não valida os algoritmos completos de animação.
Quatro testes com bytes SPU autorais cobrem padrões aceitos e rejeitados,
truncamento, desalinhamento, fonte estruturalmente diferente e padding inválido.
Falharam por ferramenta ausente antes da implementação e passaram depois.

Validação do inventário: 112 testes do projeto passaram em 7,651 s. O
executável do jogo não mudou neste incremento; checkpoint nativo permanece DCT.


## Integração em lote da família ANT comum (2026-10-26)

Foram acrescentados 39 módulos com o perfil estrutural revisado ant_common_v1,
incluindo groupnode_final_exec alcançado no último ensaio. Os dez módulos já
integrados recebem o mesmo identificador de perfil, sem alterar código, hash
ou limites anteriores. São 49 módulos comuns e 84 registros raw no manifesto.
Predictable blend (BSS 0xc30) e mirror (BSS 0x70) permanecem excluídos do perfil
0x50 e precisam de revisão específica; demais famílias também não são admitidas.

O teste em lote cruza cada manifesto com o inventário de hash fixado, verifica
os bytes do arquivo extraído e chama a CLI exclusiva de testes com os endereços
revisados. O fixture preserva o dispatch por ownership/hash da política nativa;
o caller autoral fica restrito ao processo de teste. Ele usa as bases 0, 0x8000,
0x4910 e 0x10000: 49 x 3 x 4 = 588 chamadas de construtores originais, com
código/guardas e dados relocados conferidos. Não chama substituto para main nem
atribui cobertura dos algoritmos completos de animação a esses testes.

A CLI genérica valida números, limites de alocação/fonte, alinhamento, ordem
dos construtores e separação da pilha/caller. Argumentos inválidos devem retornar
2 antes de I/O/execução. O teste novo falhou antes por zero casos admitidos,
e a CLI genérica ausente retornou 2. Critérios do incremento: tradução sem
instruções/destinos diretos pendentes, build, 588 chamadas aprovadas, regressões
anteriores e ensaio nativo estrito após o lote. FullGame compilou; todas as 588
chamadas de construtores originais passaram em 5,324 s, nas 49 imagens
conferidas por hash. Boot passou 44 testes; os 114 testes do projeto passaram
em 9,456 s. A família tem 4465 entradas nativas geradas, sem instruções ou
destinos diretos pendentes. O ensaio ant-family-native continua em validação.


Ensaio ant-family-native (1792988241346363100): saída estrita 90 aos 80,307 s.
Group final e blend node entraram no jogo; o rastreio também observou relocação
adicional de módulos existentes. O checkpoint lista precisamente os módulos
com entrada observada; não presume que os 39 novos foram todos executados.
Próximo módulo em LS 0x106e0/PC 0x10710, origem 0x2096f00, tamanho 0x10d0,
conferido integralmente em dois snapshots completos. Cinco hashes do perfil
preservados; 65 amostras de assets aprovadas. Menu e partida continuam pendentes.
Próxima ação: identificar a família do plugin em 0x2096f00 e revisar seu CRT.


## Extensão estrutural para SBU ANT e plugins adicionais (2026-10-26)

O bloqueio de 0x2096f00 é translationscaleplugin.elf, da família sbuantplugins,
com o mesmo CRT/binário de inicialização e perfil BSS 0x50 já revisados.
A revisão foi aplicada aos bytes dos demais programas reconhecidos, sem usar o
nome do diretório original como critério de aprovação. Somente 19 imagens
adicionais passaram exatamente pelas mesmas regras: plugins SBU de locomoção,
interação/contato/IK, translationscale, facial e headtrack. Nenhum limite de
código/BSS/constructores nem checagem de hash foi relaxado.

Um teste autoral novo exige que a mesma estrutura seja aceita sob rótulos de
origem diferentes e que BSS incompatível continue rejeitada. Falhou antes da
extração do revisor e passou depois. O relatório foi regenerado: 157 programas
reconhecidos, 68 com o CRT revisado. Manifesto agora tem 103 registros raw;
os 19 novos usam base canônica zero e o mesmo fixture de quatro posições.
O teste em lote exige 68 x 3 x 4 = 816 chamadas originais, sem simular main ou
algoritmos. Predictable blend/mirror continuam excluídos por BSS diferente.
Todas as traduções ficaram sem instruções ou destinos diretos pendentes.
FullGame compilou; as 816 chamadas originais passaram em 9,193 s. Os 115 testes
do projeto passaram em 9,887 s. Um reprocessamento de metadados com fonte
alterada agora remove a classificação antiga antes de revalidar, com regressão
reproduzida e aprovada. O ensaio ant-sbu-family-native segue em validação.


Ensaio ant-sbu-family-native (1792988672963477600): saída estrita 90 aos
80,653 s. Translationscale e interactionscale entraram no jogo. O próximo
plugin está em 0x2133c80, LS 0x12fa0/PC 0x12fd0, 0x2ca0 bytes, conferido
integralmente em dois snapshots completos. Ele não satisfez o perfil comum e
exige revisão específica, sem relaxar a classificação existente. Os cinco hashes
do perfil permanecem iguais e 65 amostras de assets passaram. Menu e gameplay
continuam pendentes. Próxima ação: revisar o módulo de 0x2133c80.


## Facing angle smoother com cinco construtores (2026-10-26)

O novo módulo é facinganglesmootherplugin.elf, da família fifaantplugins:
origem 0x2133c80, 0x2ca0 bytes, SHA
9866099c790cc0e579f14b42b9f4709a71b08789d9f2e944f00ea68e06841776.
Cabeçalho PIC modo 1 e entrada relativa 0x30. Diferentemente do perfil comum,
a BSS é 0x2ca0..0x38d0 (0xc30 bytes), e a tabela 0x2760..0x2774 contém cinco
construtores: 0x118, 0x8d0, 0xfe0, 0x1330 e 0x25c8, percorridos para frente.

A cauda de código segue depois do último construtor: há rotinas de matemática
até 0x2754 (bi r0) e um bloco 0x2758/0x275c que termina com branch 0x2610.
Por isso code_end é 0x2760, imediatamente antes da tabela, preservando essa
cauda. O módulo continua rejeitado pelo perfil comum; sua admissão é específica.

O fixture existente aceita quantidade de construtores e BSS explícitas para
este caso, mantendo os defaults do perfil comum. Compara toda a área de dados
e BSS e conserva as guardas após a extensão maior. São 20 chamadas originais em
quatro bases, incluindo 0x12fa0, além das regressões anteriores. A CLI ausente
retornou 2 antes da integração. A tradução gerou 100 entradas, sem instruções
nem destinos diretos pendentes. FullGame compilou; os 14 testes de construtores
passaram em 4,547 s, incluindo 20 chamadas deste módulo. Boot passou 44 testes
e os 116 testes do projeto passaram em 10,073 s. O ensaio ant-facingangle-native
segue em validação; não se afirma correção completa da suavização angular.


Ensaio ant-facingangle-native (1792989126512759400): saída estrita 90 aos
81,015 s. Facing angle smoother entrou na SPU 8193. O jogo avançou por headtrack,
ikrigtohikrig, jointtoeffector, contactpoint init/hand/foot, trajoffset IK,
interaction effector scaling e footplant pre. O rastreio registra entradas;
ainda não comprova todos os resultados desses algoritmos nem gameplay.

Próxima parada: particleikplugin.elf, origem 0x20aa380, LS 0x8390/PC 0x83c0,
0xd4c0 bytes, conferidos integralmente em dois snapshots completos. Os cinco
hashes do perfil permanecem iguais e 65 amostras de assets passaram. Próximo
incremento: três variantes ANT de BSS diferente revisadas individualmente:
particle IK, predictable blend e mirror. Menu/partida continuam pendentes.


## Três variantes ANT específicas restantes (2026-10-26)

Além de facing angle, os três plugins PIC com BSS diferente foram revisados
individualmente. Eles preservam o CRT de encaminhamento/ordem para frente,
mas não recebem o perfil ant_common_v1 de BSS 0x50/três construtores.
- particleikplugin, 0x20aa380, 0xd4c0 bytes: BSS 0x130, construtores
  0x6900/0xb610/0xbfa0/0xc310. Código até 0xc340, após o getter em 0xc320..0xc33c;
  a tabela começa em 0xc340. Inclui a posição real 0x8390 nos testes.
- predictableblendplugin, 0x20cf280, 0x3480 bytes: BSS 0xc30, construtores
  0x118/0x11a8/0x1820/0x2ab8/0x2eb8. Código até 0x2ec8; branch final 0x2ec0
  para 0x2c00, padding de oito bytes e tabela em 0x2ed0.
- mirrornode_exec, 0x2114a00, 0x21a0 bytes: BSS 0x70, construtores
  0x118/0x1958/0x1aa0/0x1d68. Código até 0x1d78; branch final 0x1d70 para
  0x1ab0, padding de oito bytes e tabela em 0x1d80.

Cada fonte confere com o hash do inventário. As CLIs ausentes retornaram 2 antes
da integração. Serão 52 chamadas originais adicionais em quatro bases, com
extensões reais de BSS e guardas, mantendo as regressões do perfil comum.
Predictable blend/mirror ainda não têm entrada real observada; a tradução visa
cobrir os módulos presentes no conteúdo offline e não presume execução deles.
As três traduções ficaram sem instruções nem destinos diretos pendentes.
FullGame compilou; os 17 testes de construtores passaram em 7,884 s, incluindo
as 52 chamadas das variantes novas. Boot passou 44 testes e os 119 testes
do projeto passaram em 10,469 s. O ensaio ant-specific-variants-native segue
em validação. As variantes têm 528/104/111 entradas nativas, respectivamente.


Ensaio ant-specific-variants-native (1792989446164060900): saída estrita 90 aos
79,515 s. Particle IK entrou e o jogo avançou por footplant post, HIK reset,
facial e face poser. Predictable blend/mirror ainda não tiveram entrada observada.
Perfil preservado pelos cinco hashes; 65 amostras de assets aprovadas.

O próximo programa está em 0x1ee9580, LS 0x80/PC 0xb0. Há 0x4f30 bytes de
imagem inicializada até LS 0x4fb0, SHA
56ac370c9307000bf6b33c207a065bedd7812ce2066b6a10faade884cb4f5a0f,
conferidos integralmente em dois snapshots. O CRT usa BSS 0x5000..0x25a60.
O identificador antigo procurou BuiltElfName muito além da imagem inicializada
e atribuiu Replay_deltacompress.elf de outra região. Essa identificação não é
válida e não será usada para traduzir o programa. Seu nome real não foi verificado.
Menu e gameplay ainda pendentes. Próximo incremento: corrigir o diagnóstico e
revisar/traduzir a imagem inicializada efetivamente carregada.
