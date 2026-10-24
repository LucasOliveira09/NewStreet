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

- Os dois executáveis foram extraídos da ISO para `private/`, com SHA-256 conferido.
- RPCS3 foi usado somente como ferramenta de obtenção dos ELF via `--decrypt`.
- O loader de ps3recomp abriu `EBOOT.elf` e `FIFAZF.elf`.
- **Duas funções reais de FIFAZF foram traduzidas e compiladas em um PE x64 nativo.**
- Os retornos inteiros passaram em **20.020 casos**, incluindo limites de inteiros.
- O runtime de ps3recomp compilou com clang-cl e seus **16 testes CTest passaram**.
- REA 6.7.0 foi instalado e executado. Recusou o ELF por arquitetura não suportada.

**O jogo completo ainda não inicia nativamente.** O executável atual é uma prova
de funções sem interface, sem partida e sem gráficos. Os testes aritméticos não
validam registradores completos, flags da CPU, SPU, RSX ou o restante do jogo.

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

Com os checkouts e dependências nas revisões fixadas:

```powershell
.\private\python-env\Scripts\python.exe .\tools\extract_targets.py 'CAMINHO\jogo.iso'
& 'CAMINHO\rpcs3.exe' --headless --decrypt "$PWD\private\EBOOT.BIN" --decrypt "$PWD\private\FIFAZF.SELF"
.\private\python-env\Scripts\python.exe .\vendor\ps3recomp\tools\ppu_loader.py .\private\EBOOT.elf -o .\private\analysis\eboot
.\private\python-env\Scripts\python.exe .\vendor\ps3recomp\tools\ppu_loader.py .\private\FIFAZF.elf -o .\private\analysis\fifazf
.\tools\build.ps1
```

A extração aceita somente os hashes dos dois SELF inspecionados. Outra edição
exige identificar os endereços novamente. A ISO é aberta somente para leitura.
`DATA3.BIG` e `DATA6.BIG` têm múltiplos extents ISO9660; o inventário soma os
registros e a extração atual se limita aos dois executáveis de extent único.

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
4. **Game runtime:** serviços, entrada real, arquivos, SPUs e renderização ainda
   não foram integrados ao FIFA Street. Passar testes do runtime não prova o jogo.

## Próximo marco técnico

Executar a inicialização real com diagnósticos que parem no primeiro serviço ou
instrução sem suporte, mantendo o ELF e os assets locais como entrada. Antes disso:

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
