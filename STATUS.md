# Checkpoint atual — 26/10/2026

Alvo: FIFA Street 2012, PS3 BLUS30882 1.00 → Windows x64 nativo.
Baseline de código do jogo: `9439c85`, branch `codex/ps3-native-bootstrap`.
A adaptação de agentes reorganiza o trabalho; não acrescenta funcionalidade ao jogo.

## Confirmado e ainda pendente

- EBOOT inicia FIFAZF como processos Windows; PPU/SPU compilados e Direct3D 12.
- Tela original do título e aviso de autosave renderizados em 1280×720.
- Start/Cross chegaram ao código original. Perfil BLUS308820000A criado e relido;
  cinco arquivos preservados por hash; SYS-DATA tem 2.127.971 bytes.
- Há artefatos na abertura. Áudio tem sinal finito; escuta e sincronia pendentes.
- **Menu navegável, cena, gameplay, partida completa e progressão não validados.**
- 99.127 entradas PPU, 369 wrappers de imports, 107 registros raw SPU.
  Contagem não comprova semântica completa dos serviços ou tarefas.
- 68 módulos ANT do perfil comum: 6.422 entradas e 816 chamadas de construtores.
  Quatro variantes específicas: 72 chamadas em quatro bases. São testes de
  inicialização/BSS/relocação, não validação integral de algoritmos de animação.

## Último ensaio do jogo

- Fonte: `reports/native-boot-checkpoint.json`; resultado privado:
  `private/analysis/ant-specific-variants-native-run.json`.
- Logs: `private/analysis/runs/1792989446164060900`.
- Saída estrita **90**, aos **79,515 s**: entrada SPU ainda não traduzida.
- Particle IK, footplant post, HIK reset, facial e face poser entraram no caminho real.
  Predictable blend/mirror foram compilados, sem entrada real observada.
- Últimos checks registrados: 44 Boot, 119 do projeto, 16 runtime CTest;
  65 amostras de assets contra oráculos independentes. Não são checks desta sessão.

## Bloqueio atual e evidência pronta

- Fonte EA **0x1ee9580**, LS **0x80**, entrada **0xb0**.
- Imagem inicializada: **0x4f30 bytes**, termina em LS **0x4fb0**.
- SHA-256: `56ac370c9307000bf6b33c207a065bedd7812ce2066b6a10faade884cb4f5a0f`.
- Todos os bytes conferem com dois snapshots completos; BSS: **0x5000..0x25a60**.
- Código revisado até **0x4a40**; dados ASCII começam nesse limite.
- CRT usa entradas adicionais **0x13c/0x154** para zerar BSS.
- Tabela de dez construtores: **0x4f80..0x4fa8**, percorrida em ordem reversa.
- Fontes privadas prontas: `private/analysis/job_1ee9580.bin`,
  `private/analysis/job_1ee9580-disassembly.txt` e snapshots em
  `private/analysis/ant-specific-variants-next-spu/spu/`.
- O diagnóstico antigo em `identified.json` atribui incorretamente
  Replay_deltacompress.elf, encontrado fora da imagem. **Nome original desconhecido.**
- Correção do identificador e tradução desta imagem continuam **pendentes**.
  Próximas etapas e aceite: `tasks/plan.md`.

## Retomada e validação proporcional

1. Confira instruções, branch/HEAD/mudanças. Leia este checkpoint e a etapa do plano.
2. Para corrigir diagnóstico: abra `tools/identify_spu_resident.py` e seus testes.
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
