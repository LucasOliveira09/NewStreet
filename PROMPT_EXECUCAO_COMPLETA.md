# Prompt para continuar o port nativo de FIFA Street

Copie o texto abaixo para o agente que terá acesso a este computador e projeto.
O pedido é implementar e validar o jogo; este documento não afirma que o port
completo já existe nem garante que a toolchain atual consiga terminá-lo.

---

Você vai assumir a engenharia do projeto FIFA Street nativo para Windows e
trabalhar na implementação, nos testes e na integração até atingir os critérios
abaixo. Leia o estado existente antes de alterar arquivos. Não responda apenas
com um plano: depois da auditoria inicial, execute a próxima tarefa técnica viável.

## 1. Objetivo e prioridade

Fazer o **FIFA Street de 2012, PS3 BLUS30882, versão 1.00**, executar como jogo
nativo de Windows x64, usando a cópia local já fornecida. A prioridade é completar
a experiência offline original disponível nesses arquivos: iniciar, navegar,
jogar, terminar partidas, progredir, salvar e retomar, com gráficos, animações,
física, controles e áudio funcionando corretamente.

A solução deve compilar o código traduzido/reconstruído e ligar os serviços
necessários a um executável Windows e seu runtime. Traduzir comandos gráficos e
implementar serviços do console faz parte da arquitetura. O executável entregue
deve funcionar sem iniciar RPCS3, Xenia ou outro emulador de console e sem usar
interpretação/JIT de CPU como substituto silencioso da recompilação pretendida.

Uma janela vazia, duas funções utilitárias, um launcher, uma animação demonstrativa
ou uma partida simulada não atendem ao objetivo. Melhorias gráficas, novas funções
e online entram depois de uma base offline correta e estável.

## 2. Caminhos e estado confirmado

Use estas variáveis e confira se continuam válidas:

```text
PROJECT_ROOT = D:\Ludevi\projetos\fifa-street-native
VIDEO_REPO   = C:\Users\Luquinhas\Desktop\RepositoriosGitHub\canal-ludevi
GAME_ISO     = D:\Luquinha\Downloads\FIFA Street (USA) (EnFrEs)\FIFA Street (USA) (En,Fr,Es).iso
RPCS3_EXE    = D:\Luquinha\Downloads\rpcs3-v0.0.43-20387-aa9ebd2f_win64_msvc\rpcs3.exe
```

O projeto técnico já tem Git iniciado, branch `codex/ps3-native-bootstrap` e commit
inicial `e96e614`. Reutilize esse histórico; verifique o HEAD e eventuais mudanças
posteriores. Não crie outro repositório dentro dele. Se estiver reconstruindo o
projeto em outra pasta sem Git, inicialize um repositório próprio antes de editar.
O repositório de vídeos continua separado.

Leia primeiro as instruções `AGENTS.md` aplicáveis, `STATUS.md` e a etapa atual
de `tasks/plan.md`; confira branch, HEAD e alterações. O estado atual é o checkpoint,
não o baseline histórico abaixo. Consulte código, testes, locks e relatórios
pertinentes à tarefa; não carregue scripts e relatórios inteiros por rotina.
Se o pedido exigir leitura integral deste documento, cumpra essa leitura.

O roteiro de modelos está em `.agents/model-routing.md`, com configuração real
em `.codex/`: somente modelos 6+, principal e no máximo um auxiliar. Preserve os
critérios de entrega e evidência abaixo ao aplicar a organização de contexto.

Baseline inicial histórico (24/10/2026), superado pelo checkpoint atual:

- Os SELF foram extraídos e os ELF obtidos usando `RPCS3 --decrypt`.
- `private/EBOOT.elf`: 74.656 bytes; `private/FIFAZF.elf`: 36.128.408 bytes.
- Ambos são ELF64 big-endian, PowerPC64 (`EM_PPC64=21`).
- O loader encontrou 9 funções candidatas no EBOOT e 54.531 no FIFAZF.
- Entrada FIFAZF: OPD `0x2143230`, código `0x23770`, TOC `0x21d5370`.
- FIFAZF importa 369 entradas de 27 bibliotecas. A varredura inicial encontrou
  224 correspondências com nomes exportados examinados. As 145 restantes não
  podem ser classificadas automaticamente como funções ausentes: revise aliases,
  bibliotecas, registradores de handlers e a semântica real de cada entrada.
- Duas funções de FIFAZF, `0x23d4c` e `0x261f0`, foram traduzidas e compiladas num
  PE x64. Retornos inteiros passaram em 20.020 casos contra um oráculo matemático.
- O runtime compilou com clang-cl e seus 16 testes CTest passaram.
- Naquele baseline inicial ainda não havia boot/frame. Hoje título e autosave
  estão validados; menu navegável e partida permanecem pendentes em `STATUS.md`.

Esses números não demonstram conformidade completa da CPU ou compatibilidade do
jogo. O teste com Unicorn 2.1.4 não completou a referência PPC64 no perfil tentado;
não reapresente os testes aritméticos como comparação contra hardware de PS3.

## 3. Git e rastreabilidade obrigatórios

Antes da primeira alteração, registre branch, HEAD e `git status`. Preserve o
trabalho existente. Use branches `codex/` quando uma nova branch fizer sentido.

Faça commits locais pequenos, com propósito claro, depois de cada incremento
verificado. Versione todo código autoral necessário: runtime/adaptadores próprios,
scripts, configuração, testes, documentação, patches e locks. Antes de cada commit,
revise o diff staged, execute os checks pertinentes e `git diff --cached --check`.
Não misture mudanças de terceiros ou do repositório de vídeos no commit técnico.

`private/` contém ISO, SELF, ELF, assets, código derivado e builds locais.
`vendor/` contém checkouts externos. Preserve a exclusão desses diretórios e de
credenciais, chaves, dumps e binários do jogo. "Commitar tudo" significa registrar
todo trabalho técnico necessário para reproduzir o projeto, mantendo esses dados
locais fora do histórico.

Se modificar uma dependência ignorada em `vendor/`, registre a mudança como patch
versionado e aplicado automaticamente sobre uma revisão fixa, ou use um fork
referenciado por commit. Uma alteração essencial solta em pasta ignorada é uma
pendência de entrega. Preserve licenças e créditos dos componentes reaproveitados.

Mantenha o histórico local; este pedido não inclui publicação de um repositório
remoto. Ao encerrar uma sessão, informe commits, alterações ainda não commitadas,
checks executados e como retomar.

## 4. Ferramentas e evidências

Parta das revisões em `toolchain.lock.json`. No ambiente preparado há Node
24.22.1, REA 6.7.0, LLVM/clang-cl 23.1.4, Python isolado, CMake/Ninja e SDK de
Windows via Visual Studio. O build MSVC puro falhou; clang-cl compilou.

Reproduza o baseline com `tools/build.ps1`. Não reinstale tudo nem atualize
dependências indiscriminadamente. Confirme opções pelo `--help`, código e docs da
revisão usada: já há divergências entre guias antigos e as CLIs atuais.

Use REA onde houver suporte comprovado. A versão registrada recusou este ELF
PPC64; configurar Ghidra não elimina essa restrição. Para análise de PS3, valide
um loader e linguagem adequados a Cell/PPU, incluindo extensões VMX, e ferramentas
específicas para SPU. Não altere o cabeçalho para fingir outra arquitetura.

RPCS3 pode servir para obter material de análise e observar o comportamento de
referência. Não conte sua execução como entrega nativa. Verifique bytes e
endereços antes de usar descompilação, nomes inferidos ou sugestões de IA.

Consulte as fontes oficiais fixadas no final deste documento. Quando docs e
implementação divergirem, registre o conflito e confirme pelo comportamento real.

## 5. Sequência de implementação

Execute os marcos abaixo em incrementos pequenos. Atualize o checklist com fatos
e dependências descobertas; a lista não implica que todos os subsistemas já tenham
suporte na ferramenta candidata.

### A. Reproduzir a base e completar o inventário

Confira hashes, hardware, versão de Windows, GPU/driver e versões das ferramentas.
Reproduza o build e os testes. Identifique executáveis adicionais, módulos PRX,
overlays, tarefas SPU, arquivos e configuração exigidos pelo boot.

Revise o fluxo EBOOT/FIFAZF. Decida com evidências se o bootstrap deve reproduzir
o launcher ou inicializar FIFAZF com seus argumentos, contexto e dados equivalentes.
Não presuma que basta despachar o endereço de entrada.

Complete a extração de assets necessária preservando a ISO. Trate arquivos
ISO9660 de múltiplos extents: DATA3.BIG e DATA6.BIG já apresentam esse caso.
Mapeie BH/BIG/SDAT/VIV conforme os arquivos reais. Se dados comprimidos ou
protegidos exigirem material que não existe localmente, registre o requisito e
continue as frentes independentes; não substitua por assets fictícios.

Aceite: baseline reproduzido e manifesto rastreável dos arquivos e módulos do boot.

### B. Executar a cadeia de inicialização PPU

Integre segmentos ELF, BSS, endianness, alinhamento, ponteiros guest/host,
stack, TLS, TOC, OPD, contexto da PPU e dispatch de chamadas diretas/indiretas.
Trate a diferença entre os registros de 64 bits e a ABI/endereço efetivo usada.

Traduza primeiro o caminho de inicialização; amplie a cobertura conforme o fluxo
real exigir. Verifique fronteiras, jump tables, tail calls, imports e eventuais
relocações de módulos adicionais. Compile em unidades pequenas e reutilize cache.
Valide operações inteiras, flags, floating point e VMX necessárias ao caminho.

Toda instrução, syscall, função ou chamada indireta sem suporte deve gerar um
diagnóstico com módulo, endereço e contexto suficientes. Evite loops de retry,
saltos arbitrários e alterações de retorno apenas para passar da tela de erro.

Aceite: execução identificável de inicialização real do jogo no processo Windows,
com rastreamento até uma etapa conhecida ou até o primeiro bloqueio reproduzível.
Um bloqueio diagnosticado é progresso parcial, não conclusão do marco completo.

### C. Implementar serviços usados pelo jogo

Resolva imports com biblioteca/NID, ABI e wrappers corretos. Audite os handlers
do upstream antes de considerá-los implementados: alguns podem ser stubs.
Não fabrique `CELL_OK`, arquivos, callbacks ou resultados para encobrir ausência.
Um serviço opcional pode retornar indisponibilidade de forma compatível, com isso
documentado e validado no fluxo offline.

Implemente os serviços efetivamente alcançados: memória e alocação, arquivos e
mounts, sincronização, threads, TLS, eventos, tempo, callbacks de sistema, saves,
entrada, áudio e dependências de módulos. Garanta tradução de ponteiros, estruturas
big-endian e ownership. Serviços de rede/conta não podem bloquear o modo offline;
preserve respostas coerentes quando recursos externos estiverem indisponíveis.

Aceite: inicialização e carregamentos avançam com serviços de comportamento
verificado, sem corrupção de memória ou sucesso inventado em caminho necessário.

### D. Integrar as tarefas SPU necessárias

Identifique como o jogo carrega, seleciona e agenda programas SPU/SPURS e overlays.
Implemente/traduza as tarefas alcançadas, local store, canais, DMA, tags, mailbox,
eventos, atomics e sincronização com a PPU. Não suponha a função de uma tarefa
apenas pelo nome; compare dados de entrada, saída e ordem das operações.

Aceite: tarefas necessárias ao carregamento e gameplay produzem resultados e
completam sem bypass, perda de dados, deadlock ou dependência do emulador.

### E. Produzir o primeiro frame e os menus reais

Audite o backend RSX disponível na revisão do runtime. Escolha um backend Windows
com suporte real no hardware de teste; Direct3D 12 é candidato, não garantia.
Integre command buffers, memória de GPU, fences/semaphores, shaders, texturas,
formatos comprimidos, render targets, depth, blending, viewport e apresentação.
Implemente o que estiver ausente. Preserve cache e diagnóstico de shaders.

Confirme o primeiro frame produzido pelo fluxo real do jogo, depois fontes,
interface, vídeos quando usados, menus e carregamento de uma cena. Compare com
referência visual e registre o cenário de cada captura.

Aceite: menu original navegável e cena real renderizada corretamente; uma janela,
um clear de cor ou uma captura exibida como imagem não satisfazem esse critério.

### F. Completar uma partida offline

Integre controles com controle físico e entrada de PC apropriada, áudio e timing.
Valide jogadores, bola, física, colisões, animações, câmera, regras, placar,
pausa, fim de partida e retorno ao menu. Verifique replay quando disponível.

Aceite: uma partida completa do início ao fim com interação real, áudio e imagem
sincronizados, sem atalhos que substituam a lógica do jogo.

### G. Cobrir o conteúdo offline e a persistência

Inventarie os modos e conteúdos presentes na cópia fornecida. Valide seleção de
equipes/arenas, opções, World Tour e demais modos identificados, personalizações
quando presentes, progressão, desbloqueios e fluxos de volta aos menus.

Teste criação, gravação, carregamento, reinício do processo, continuidade da
progressão, erros de escrita e preservação do save anterior. DLC entra somente
quando seus arquivos e requisitos estiverem disponíveis. Liste separadamente
recursos que dependiam de servidores originais e o que continua pendente.

Aceite: matriz de funcionalidades offline com evidência de todos os itens exigidos;
uma partida rápida funcional não equivale ao jogo completo.

### H. Estabilidade, desempenho e instalação reproduzível

Meça frametime, uso de CPU/GPU/memória, tempos de loading e compilação de shaders
em cenários fixos, documentando hardware, resolução e configuração. Corrija
gargalos medidos. Preserve velocidade da simulação ao alterar resolução ou FPS;
não prometa 60 FPS se isso ainda não foi medido e validado.

Teste várias partidas consecutivas, reinício, mudança de cenário, foco da janela,
redimensionamento e retomada. Se não houver automação de gameplay confiável,
execute testes manuais reais e registre exatamente o que foi observado.

Crie preparação/build/execução documentados e reproduzíveis a partir de checkout
limpo mais os dados locais do usuário. Fixe dependências e hashes, aplique patches
automaticamente e detecte arquivos ausentes com mensagens úteis. O programa deve
funcionar sem depender da pasta de Downloads, do ambiente do desenvolvedor ou
de caminho absoluto do Lucas embutido no código de produção.

Aceite: build independente do diretório de desenvolvimento, distribuição local
testada e matriz final sem falhas críticas abertas. Declare o alcance dos testes;
validar este PC não prova compatibilidade com todo hardware Windows.

## 6. Papel do ReStreet

O checkout `vendor/restreet` serve como referência técnica e possível ponto de
partida para online futuro. Ele usa os executáveis da edição Xbox 360 e ReXGlue;
não alimenta esse pipeline diretamente com a nossa ISO de PS3.

Estude o que for transferível, preserve créditos e licenças e documente diferenças
de módulos, ABI e runtime. Não troque a origem do projeto por Xbox 360, baixe outra
edição, instale um release pronto ou anuncie um port alheio como implementação
própria. Se a base PS3 se mostrar inviável, apresente o bloqueio e o custo das
alternativas antes de propor mudança de plataforma.

Online não deve atrasar boot, gráficos, partida e progressão offline.

## 7. Método de trabalho e encerramento

Mantenha `tasks/plan.md`, `tasks/todo.md` e um `STATUS.md` atualizado. Para cada
incremento registre problema concreto, hipótese, evidência, arquivos alterados,
teste aplicado, resultado e commit. Reaproveite os padrões existentes e evite
reestruturar o projeto por estética enquanto o boot estiver pendente.

Progrida autonomamente dentro deste escopo. Uma limitação do REA, um erro de
compilação ou o tamanho do trabalho não encerram a investigação. Mude para uma
ferramenta compatível, corrija a causa ou avance em uma dependência independente.
Se houver bloqueio que realmente exija material ou decisão do usuário, forneça
o comando que falha, evidência, requisito exato e trabalho já concluído. Não
invente que a função existe, que uma tela abriu ou que uma partida foi testada.

Ao terminar uma sessão, deixe o código autoral e a documentação relevante
commitados, com o hash informado, e uma instrução concreta de retomada. Não
declare conclusão só porque os testes de unidade passaram. Não prometa execução
em segundo plano quando o agente não estiver trabalhando.

Só declare **port completo** quando o executável nativo atender à matriz offline,
com boot, menu, partidas, áudio, controles, saves, progressão e instalação
reproduzível validados, e quando os limites remanescentes estiverem explícitos.
Se houver requisito obrigatório pendente, declare o marco efetivamente alcançado.

Comece conferindo o repositório e o checkpoint atual. Execute a etapa vigente de
`tasks/plan.md`, reproduzindo somente a falha ou o baseline pertinente à mudança.
Não reinicie marcos já concluídos sem uma regressão ou outra razão verificável.

## Fontes da base técnica

- Pipeline PPU e runtime: https://github.com/sp00nznet/ps3recomp/blob/a6d76c895f77eb30b90a806c830544e61821b77f/docs/PPU_RECOMP.md
- Admissão PowerPC no REA: https://github.com/morluto/rea/blob/b869fa762a827fb66978067fabe09439ebfef111/docs/ghidra-ppc.md
- Build do ReStreet: https://github.com/samuelit0davila/fifa-street-pc-port/blob/a4be1d0a22c330d64d540cbf6681edbf6a8d4f7b/docs/BUILDING.md
- CLI RPCS3 usada na preparação: https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/rpcs3.cpp

Use essas fontes para entender as interfaces da base. Os critérios do projeto
acima são requisitos de implementação e validação, não promessas dessas ferramentas.
