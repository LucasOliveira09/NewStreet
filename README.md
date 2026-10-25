# FIFA Street: investigação do port nativo para Windows

Alvo: FIFA Street (2012), PS3 **BLUS30882, versão 1.00**. Prioridade do Lucas:
rodar o jogo nativamente no Windows; depois melhorar gráficos e adicionar funções.
Multiplayer fica para uma etapa posterior. A investigação começou em 24/10/2026.

## Prompt de continuidade

O [prompt completo de execução](PROMPT_EXECUCAO_COMPLETA.md) reúne contexto,
requisitos, marcos, validação e disciplina de commits para o agente que assumir
o port. O [plano](tasks/plan.md) e o [checklist](tasks/todo.md) organizam a retomada.
Preparar esses documentos não altera o estado de implementação descrito abaixo.

## Resultado atual

**Execução nativa parcial:** EBOOT inicia FIFAZF em outro processo Windows,
com código PPU/SPU compilado e backend Direct3D 12. A tela original do título
e o aviso de autosave foram renderizados; Start e Cross chegaram ao código
original, que gravou o primeiro perfil `BLUS308820000A`, incluindo `SYS-DATA`.
O diagnóstico atualizado está em `reports/native-boot-checkpoint.json` e o
histórico de correções em `STATUS.md`. Menu navegável, partida e progressão
ainda precisam de validação. A abertura tem artefatos gráficos conhecidos.

O patch em `patches/0001-strict-native-boot.patch` faz o alvo de boot parar em
imports, syscalls, funções e instruções sem suporte, em vez de fabricar sucesso.
`tools/apply_patches.py` aplica o patch à revisão fixada e aceita reaplicação.

- Os dois executáveis foram extraídos da ISO para `private/`, com SHA-256 conferido.
- RPCS3 foi usado somente como ferramenta de obtenção dos ELF via `--decrypt`.
- O loader de ps3recomp abriu `EBOOT.elf` e `FIFAZF.elf`.
- O alvo FullGame contém 99.127 entradas nativas PPU e 369 stubs de imports.
- O probe aritmético separado cobre duas funções reais em **20.020 casos**.
- O runtime de ps3recomp compilou com clang-cl e seus **16 testes CTest passaram**.
- REA 6.7.0 foi instalado e executado. Recusou o ELF por arquitetura não suportada.

**O port completo continua pendente.** O primeiro save escrito não comprova
persistência de todos os modos ou uma partida funcional. As provas aritméticas
e os testes do runtime também não equivalem a conformidade completa do PS3.

## Evidências

| Parte | Observação local |
|---|---|
| `EBOOT.BIN` | 77.088 bytes, SELF retail; ELF obtido com 74.656 bytes |
| `FIFAZF.SELF` | 36.130.840 bytes; ELF obtido com 36.128.408 bytes |
| Arquitetura | ELF64 big-endian, `EM_PPC64=21`, `ET_EXEC=2` |
| EBOOT | 9 funções candidatas, 32 imports de 6 bibliotecas; contém referência a `fifazf.self` |
| FIFAZF | 54.531 funções candidatas, 71.491 descritores OPD; 369 imports de 27 bibliotecas |
| Entrada FIFAZF | descritor `0x2143230`, código `0x23770`, TOC `0x21d5370` |
| Auditoria inicial | 224/369 imports correspondem a nomes exportados examinados; 145 sem correspondência nessa varredura |

Contagens são resultados do loader, não uma revisão individual de cada função.
Correspondência de NID não comprova que o serviço esteja implementado ou correto.
O cabeçalho legível dentro de um SELF não era, sozinho, o código pronto para análise.

As funções em `0x23d4c` e `0x261f0` comportam-se, nos testes, como valor absoluto
inteiro de 32 e 64 bits, preservando o comportamento de overflow no mínimo inteiro.
Esses são nomes descritivos inferidos; não recuperamos os nomes originais.
`probe_manifest.json` fixa o hash do ELF e os endereços.

## Organização

- `tools/`: extração limitada, tradução, build e auditoria reproduzíveis.
- `tests/`: harness nativo e testes contra o cálculo matemático independente.
- `reports/`: evidências selecionadas; logs completos ficam locais.
- `private/`: executáveis originais, ELF, código derivado, ambientes e builds. Ignorado no Git.
- `vendor/`: checkouts de REA, ps3recomp e ReStreet. Revisões em `toolchain.lock.json`.

Nenhum arquivo de jogo, asset ou código traduzido do jogo está versionado aqui.
O repositório de vídeos permanece separado em
`C:/Users/Luquinhas/Desktop/RepositoriosGitHub/canal-ludevi`.

## Repetir no ambiente preparado

No PowerShell, dentro desta pasta:

```powershell
# Repete tradução, build do probe, build do runtime e testes.
.\tools\build.ps1

# Apenas a prova de funções.
.\tools\build.ps1 -Target Probe

# REA instalado localmente; este comando apenas exibe a versão.
.\tools\rea.ps1 --version

# Auditoria estática dos imports do executável maior.
.\private\python-env\Scripts\python.exe .\tools\audit_target.py
```

Saídas: `private/build/probe/fifa_function_probe.exe` e
`private/build/runtime-clang/ps3recomp_runtime.lib`.
O probe recebe um endereço de função e valores hexadecimais via stdin; os testes
automatizados exercitam as duas funções. Ele não é um executável jogável.

## Repetir a preparação dos arquivos

O extrator completo de `PS3_GAME` está disponível:

```powershell
.\private\python-env\Scripts\python.exe .\tools\extract_disc.py 'CAMINHO\jogo.iso'
```

A extração usa a visão UDF, incluindo a partição de metadados UDF 2.50 do disco.
Ela preserva `data0.big.sdat`; a visão ISO9660 chama esse mesmo conteúdo de
`DATA0_BIG.SDAT`, nome que o jogo não encontra. Não renomeie arquivos por palpite.
`--filesystem iso9660` permanece disponível para diagnóstico explícito.

`tools/run_native.py --timeout 30 --capture --observe-assets` grava entradas e
saídas de até 32 tarefas por codec na pasta privada de cada tentativa. O relatório
compara os bytes produzidos pelas traduções SPU com RefPack independente e zlib
do Python (DEFLATE raw). O observador não fornece dados ao jogo. A execução de
referência conferiu 47 tarefas, totalizando 2.671.706 bytes de saída, sem diferenças;
isso cobre essas capturas, sem provar todos os jobs ou os caminhos de gameplay.

A extração local produziu 104 arquivos (4.800.945.013 bytes), com hashes por arquivo
em `private/disc/extraction-manifest.json`. Os extents repetidos de DATA3.BIG e
DATA6.BIG foram concatenados na ordem do diretório. O leitor abre a ISO somente
para leitura, valida os limites e as cópias de endianness dos registros. Cinco
testes sintéticos exercitam concatenação, corrupção de registros e nomes inválidos.
O diretório de saída é restrito a `private/` e arquivos existentes são comparados
com os bytes da ISO antes de serem reutilizados.

Com os checkouts e dependências nas revisões fixadas:

```powershell
.\private\python-env\Scripts\python.exe .\tools\extract_targets.py 'CAMINHO\jogo.iso'
& 'CAMINHO\rpcs3.exe' --headless --decrypt "$PWD\private\EBOOT.BIN" --decrypt "$PWD\private\FIFAZF.SELF"
.\private\python-env\Scripts\python.exe .\vendor\ps3recomp\tools\ppu_loader.py .\private\EBOOT.elf -o .\private\analysis\eboot
.\private\python-env\Scripts\python.exe .\vendor\ps3recomp\tools\ppu_loader.py .\private\FIFAZF.elf -o .\private\analysis\fifazf
.\tools\build.ps1
```

A extração limitada de `extract_targets.py` aceita somente os hashes dos dois SELF inspecionados. Outra edição
exige identificar os endereços novamente. A ISO é aberta somente para leitura.
`DATA3.BIG` e `DATA6.BIG` têm múltiplos extents ISO9660; o inventário soma os
registros; `extract_disc.py` extrai a árvore inteira, preservando os nomes UDF.

Node 24.22.1 e LLVM 23.1.4 foram instalados de forma portátil dentro de `private/`.
O SDK e os headers de Windows vêm do Visual Studio 2026 já instalado.
Hashes e revisões estão no lock; `requirements.lock.txt` registra o ambiente Python.
Não há instalador automático para uma máquina vazia nesta etapa.

## Limites encontrados

1. **REA:** o comando `analyze` recusou o ELF64/PPC64 antes de usar Ghidra.
   A inspeção de layout por pwntools também está limitada a Linux x64 nessa versão.
   O doctor reportou provedores/configurações ausentes; não registramos um MCP
   global nem configuramos Ghidra. Instalar Ghidra não altera a recusa de arquitetura.
2. **Compilador:** MSVC puro falhou em builtins atômicos do runtime. Clang-cl
   23.1.4 resolveu a compilação. A documentação e mensagens do upstream divergem
   sobre suporte MSVC; o build local determina a escolha registrada.
3. **Validação:** tentamos Unicorn 2.1.4 como referência PowerPC64, mas ele não
   completou a função no perfil testado. A prova aceita usa o oráculo matemático
   descrito nos testes; não declaramos comparação completa contra CPU de PS3.
4. **Game runtime:** há renderização e tarefas SPU reais em processos Windows
   nativos. Serviços e programas novos continuam sujeitos a bloqueios explícitos.
   Gameplay, fidelidade gráfica completa e persistência de progressão não foram
   validados. Passar testes não prova o jogo.

## Próximo marco técnico

O boot nativo já executa a troca EBOOT -> FIFAZF. O host usa `CreateProcessW`,
preserva o vetor de argumentos e propaga o código de saída do filho. Nenhum
emulador é iniciado. O callback de encerramento do EBOOT também é executado.

```powershell
.\tools\build.ps1 -Target Boot
.\tools\build.ps1 -Target Game -StartupLimit 512
.\private\python-env\Scripts\python.exe tools/run_native.py --profile startup

# Cobertura ampliada por OPD + chamadas e fronteiras descobertas.
.\tools\build.ps1 -Target Spu
.\tools\build.ps1 -Target FullGame -WithSpu -Jobs 6
.\private\python-env\Scripts\python.exe tools/run_native.py --profile full

# Recompilar adaptadores sem repetir a geração já existente.
.\tools\build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 6
```

O perfil `FullGame` usa `/Od` para reduzir o ciclo de investigação inicial.
`-OptimizeFullGame` seleciona `/O1`; medir desempenho somente após validar o
caminho funcional. O host também registra exceções nativas em `[fifa-crash]`,
incluindo símbolo/endereço do Windows e o contexto PPU disponível.

A geração SPU admite somente programas revisados; o inventário permanece parcial.
O runtime para em programa ou salto SPU ausente antes de usar interpretação ou
concluir uma tarefa sem código.
O teste compilado do gerador cobre dois segmentos separados e seu salto entre
segmentos. Ligar essas imagens ao executável ainda não valida sua execução no jogo.
O mesmo alvo `Spu` gera os overlays raw revisados, com hashes e limites em
`spu_overlays.json`. Há filtros de áudio PIC executados em diferentes posições
de local store. O registro verifica bytes e endereço de carga antes
de permitir a execução e invalida traduções quando as instruções são substituídas.

O registro PRX mantém os exports reais por biblioteca, NID e tipo (função ou
variável). A chamada de uma função exportada usa seu OPD, preserva os argumentos
do contexto e restaura o TOC do chamador. Isso ainda não implementa o carregamento
e as relocações de um SPRX adicional. ABI consultada no
[loader de módulos do RPCS3 aa9ebd2f](https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/PPUModule.cpp)
e no [serviço de registro](https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/Emu/Cell/lv2/sys_prx.cpp).

O gerador usa a descoberta de jump tables do SDK para manter cases internos e
seu epílogo compartilhado. `tools/check_switch_lowering.py` monta uma rotina
PowerPC autoral com Keystone 0.9.2, recompila para x64 e testa seis entradas,
incluindo o caminho padrão e a preservação de pilha/r31. Esse teste faz parte
de `-Target Boot`; Keystone é dependência de teste, não intérprete do jogo.
Os chunks do FIFAZF seguem faixas de bytes do guest, com tabela separada.
A descoberta revisita funções divididas por novos alvos até estabilizar suas
fronteiras. Três testes cobrem esse caso, loops e limite de seleção. Os roots
observados aceitos são versionados em `startup_roots.json` e conferidos por hash
do ELF; observações privadas adicionais continuam disponíveis no cache local.

O host inicia D3D12 e o relógio/consumidor FIFO somente após o GCM do jogo.
A inicialização do backend foi confirmada na RX 580 2048SP, a 1280x720.
O jogo começou a ler seus assets; ainda não produziu um frame validado.
`tools/run_native.py --capture` habilita readback do primeiro frame do backend
com operações de desenho. As capturas ficam no diretório privado da tentativa.
`--syscall-trace` habilita o log detalhado de syscalls, desativado por padrão.
Em uma falha SPU, a tentativa preserva o local store e os registradores em
`private/analysis/runs/<tentativa>/spu`, sem alterar ou interpretar seu código.
O runner mantém cache e dados graváveis em `private/userdata/dev_hdd0` e
`dev_hdd1`. `PS3_HDD0_ROOT` e `PS3_HDD1_ROOT` podem selecionar outras raízes;
o host aplica os mesmos mounts ao adaptador PPU e às APIs genéricas de arquivos.

As saídas por tentativa ficam em `private/analysis/runs`. Código 90 sinaliza um
bloqueio explícito; 92 é somente captura da solicitação de troca sem filho
configurado. A ferramenta de diagnóstico registra esses resultados sem declará-los
como sucesso do jogo. O perfil ampliado não prova cobertura de todo código indireto.

Próximos passos, mantendo o ELF e os assets locais como entrada:

1. Revisar o fluxo `EBOOT -> FIFAZF`, as entradas e as importações do boot.
2. Traduzir a cadeia necessária ao boot e ligar os handlers e o dispatcher.
3. Resolver imports pelo par biblioteca/NID e documentar aliases e stubs.
4. Implementar os serviços efetivamente alcançados; evitar sucesso fictício.
5. Registrar separadamente: código do jogo executado, primeira janela,
   primeiro frame real, menu e primeira partida.

Não há estimativa confiável para concluir todos os modos ou garantir funcionamento
perfeito. A meta permanece um jogo nativo funcional; esta entrega registra apenas
o primeiro marco comprovado.

## ReStreet e fontes

[ReStreet](https://github.com/samuelit0davila/fifa-street-pc-port) foi clonado como
referência para trabalho já feito e possível online futuro. Seu pipeline usa a
edição Xbox 360 e ReXGlue: nossa ISO de PS3 não é entrada intercambiável. O online
e o gameplay desse projeto não foram executados ou verificados neste computador.

- [REA: admissão PowerPC](https://github.com/morluto/rea/blob/main/docs/ghidra-ppc.md).
- [ps3recomp: pipeline PPU](https://github.com/sp00nznet/ps3recomp/blob/master/docs/PPU_RECOMP.md).
- [ps3recomp: preparação do ELF](https://github.com/sp00nznet/ps3recomp/blob/master/docs/GETTING_STARTED.md).
- [RPCS3 aa9ebd2f: CLI e decrypt](https://github.com/RPCS3/rpcs3/blob/aa9ebd2f/rpcs3/rpcs3.cpp).
- [ReStreet: build](https://github.com/samuelit0davila/fifa-street-pc-port/blob/main/docs/BUILDING.md).

Revisões locais exatas em `toolchain.lock.json`; as URLs de branches explicam o
pipeline, enquanto os arquivos dos checkouts fixados registram o que foi usado.
