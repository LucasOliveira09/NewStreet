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
