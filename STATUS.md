# Checkpoint atual — 26/10/2026

Alvo: FIFA Street 2012, PS3 BLUS30882 1.00 → Windows x64 nativo.
Branch: `codex/ps3-native-bootstrap`; incremento atual: CRT fixo e Replay MatrixSave.
Identificação SPU delimitada corrigida; novo módulo entrou no caminho real.

## Confirmado e ainda pendente

- EBOOT inicia FIFAZF como processos Windows; PPU/SPU compilados e Direct3D 12.
- Tela original do título e aviso de autosave renderizados em 1280×720.
- Start/Cross chegaram ao código original. Perfil BLUS308820000A criado e relido;
  cinco arquivos preservados por hash; SYS-DATA tem 2.127.971 bytes.
- Há artefatos na abertura. Áudio tem sinal finito; escuta e sincronia pendentes.
- **Menu navegável, cena, gameplay, partida completa e progressão não validados.**
- 99.127 entradas PPU, 369 wrappers de imports, 109 registros raw SPU.
  Contagem não comprova semântica completa dos serviços ou tarefas.
- 68 módulos ANT do perfil comum: 6.422 entradas e 816 chamadas de construtores.
  Quatro variantes específicas: 72 chamadas em quatro bases. São testes de
  inicialização/BSS/relocação, não validação integral de algoritmos de animação.

## Último ensaio do jogo

- Fonte: `reports/native-boot-checkpoint.json`; resultado privado:
  `private/analysis/replay-matrixsave-native-run.json`.
- Logs: `private/analysis/runs/1793030862357211100`.
- Saída estrita **90**, aos **82,044 s**: outra entrada SPU ainda não traduzida.
- Particle IK, footplant post, HIK reset, facial e face poser entraram no caminho real.
  Predictable blend/mirror foram compilados, sem entrada real observada.
- Últimos checks registrados: 44 Boot, 131 do projeto, 16 runtime CTest;
  65 amostras de assets contra oráculos independentes. Runtime CTest é registro anterior; os demais checks foram executados neste incremento.

## Incremento validado e próximo bloqueio

- `job_raw_1ee9580`: fonte 0x1ee9580, base 0x80, entrada 0xb0,
  0x4f30 bytes e 173 entradas nativas, sem instruções/destinos diretos pendentes.
- CRT original zerou BSS 0x5000..0x25a60 e executou dez construtores em ordem
  reversa, preservando código e guardas. Fixture para antes de main; o ensaio
  do jogo usa seus argumentos originais e confirmou entrada real do módulo.
- Nome original desse módulo segue desconhecido. Identificador corrigido não
  atribui mais o rótulo distante Replay_deltacompress.elf.
- Replay_matrixsave.elf, fonte 0x1f23500: 78 entradas nativas e CRT vazio
  validado, preservando imagem e guardas. Entrada real observada no último ensaio.
- Próxima imagem: **Replay_matrixload.elf**, fonte **0x1f1f880**, LS **0x80**,
  entrada **0xb0**, **0x3be0 bytes**, conferidos integralmente em dois snapshots.
- SHA-256: `00e35e03ec4bb7d52a9ac86b226d15e60e8bf3c79c5413a4c34081553ccbfc7e`.
- Nome está exatamente na fronteira declarada, não em busca distante.
- Cabeçalho flags **0x80000080**, modo **0**: não admitir como PIC modo 1.
- Snapshots: `private/analysis/replay-matrixsave-next-spu/spu/`.
- Identificação: `private/analysis/replay-matrixsave-next-identified.json`.
- Próximo incremento: revisar CRT/limites e traduzir para a base fixa observada.

## Retomada e validação proporcional

1. Confira instruções, branch/HEAD/mudanças. Leia este checkpoint e a etapa do plano.
2. Consulte a imagem Replay_matrixload e seus limites; diagnóstico já foi corrigido.
3. Para tradução: confira bytes, fronteiras e manifesto; só depois gere e compile.
4. O principal é dono exclusivo de lift/build/probe/patch/commit. Nunca relinke
   enquanto um processo nativo pai ou filho estiver vivo.

Comandos a partir da raiz (escolha conforme a mudança, não execute todos por rotina):

```powershell
private/python-env/Scripts/python.exe tools/check_agent_setup.py
private/python-env/Scripts/python.exe -m unittest discover -s tests
./tools/build.ps1 -Target Boot
./tools/build.ps1 -Target Runtime
./tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4
```

Novo manifesto SPU exige lift antes do build; SkipLift só reutiliza saídas atuais.
Use `tools/run_title_probe.py --help` para ensaio oculto; mantenha ROIs e tempos
já revisados. Leia logs vivos por trechos limitados de bytes, nunca Tail contínuo.

## Referências e continuidade

- Critérios completos: `PROMPT_EXECUCAO_COMPLETA.md`; entrega: `tasks/todo.md`.
- SDK fixado em `a6d76c895f77eb30b90a806c830544e61821b77f`;
  mudanças reproduzíveis em `patches/0001-strict-native-boot.patch`.
- Kit adaptado: `AGENTS.md`, `.agents/model-routing.md` e `.codex/`.
- Histórico anterior preservado com hashes em `docs/history/manifest.json`.
- Substitua este checkpoint ao avançar; não volte a acrescentar um diário inteiro.
