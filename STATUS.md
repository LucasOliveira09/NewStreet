# Checkpoint atual — 26/10/2026

Alvo: FIFA Street 2012, PS3 BLUS30882 1.00 → Windows x64 nativo.
Branch: codex/ps3-native-bootstrap. Incremento atual: route PIC com entrada d8.
Estado detalhado e histórico técnico: reports/native-boot-checkpoint.json e Git.

## Confirmado

- EBOOT inicia FIFAZF como processos Windows; PPU/SPU compilados e Direct3D 12.
- Título original e aviso de autosave renderizados em 1280×720.
- Start/Cross chegaram ao código original. Perfil BLUS308820000A criado/relido;
  cinco arquivos preservados por hash; SYS-DATA tem 2.127.971 bytes.
- Há artefatos na abertura. Áudio tem sinal; escuta/sincronia ainda pendentes.
- **Menu navegável, cena, gameplay e partida completa ainda não validados.**
- 99.127 entradas PPU, 369 wrappers de imports, 122 registros raw SPU.
  Contagem não demonstra semântica completa dos serviços ou algoritmos.

## Último ensaio e verificações

- Resultado: private/analysis/route-native-run.json.
- Logs: private/analysis/runs/1793041233048875700.
- Saída estrita **90**, aos **82,270 s**, import NP sem implementação.
- Route entrou no caminho real; algoritmo completo não foi validado.
- 44 testes Boot, 142 do projeto e 65 amostras de assets passaram.
- 16 runtime CTest são registro anterior; runtime não foi alterado neste incremento.
- Os cinco hashes do perfil permanecem iguais ao checkpoint JSON.

## Incrementos recentes validados

- ANT: 68 módulos comuns/816 chamadas de construtores e quatro variantes/72;
  testes de CRT/BSS/relocação, sem afirmar todos os algoritmos de animação.
- job_raw_1ee9580: 173 entradas, dez construtores reversos e BSS; entrada real.
  Nome original desconhecido; rótulo distante Replay_deltacompress era inválido.
- Replay_matrixsave/Matrixload: 78/189 entradas, CRT e constantes; entradas reais.
- FIFARNA batchplayer pass0: 477 entradas, BSS448, dois construtores; entrada real.
- Railtracks path estimates: 1.769 entradas, BSS25072, quatro construtores,
  retorno ao stop0 original incluído e testado; entrada real.
- User music arbiter: 19 entradas PIC; init4bases e 4.096 amostras de fade
  contra oráculo linear em dois canais; código/guardas preservados; entrada real.
- Compressor1: 114 entradas PIC; init4bases, callbacks/contexto/guardas validados;
  entrada real, algoritmo completo de compressão não validado.
- Reverb1: 287 entradas PIC; init4bases/callbacks/contexto/guardas e 32 bytes de
  estado preservados; entrada real, algoritmo de reverberação não validado.
- Matrix panner: 26 entradas PIC; init4bases/callbacks/guardas validados; entrada real.
- Delay: 96 entradas PIC; init4bases/callbacks/contexto/guardas validados; entrada real.
- Lote DSP: FIR64/IIR2/clip têm 82/44/21 entradas e init4bases cada; ainda sem entrada real.
- Reverb IR1: 391 entradas, init4bases/208bytes de estado preservados; entrada real.
- Identificador preserva diagnósticos de JSONs truncados e analisa os válidos.

## Bloqueio atual

- Serviço **sceNpBasicGetMessageEntryCount**, NID **0xecd503de**.
- Thread23, LR15f2564, import PC2147978; tipo6, destino countd01871a0.
- Implementar erros reais da consulta offline, preservando o destino em falhas.
- Route: 64 entradas PIC, entryd8, init4bases/callbacks/contexto/guardas validados;
  entrada real confirmada. Fonte1ffb680, SHA registrado no checkpoint JSON.
- Próxima ação: reproduzir o contrato NP com testes de init/argumentos/offline;
  executar novo ensaio nativo para avançar ao menu/partida.

## Retomada e comandos

Leia AGENTS.md, este checkpoint e a etapa de tasks/plan.md. Abra só os arquivos
pertinentes. O principal é dono de lift/build/probe/patch/commit, serializados.
Nunca relinke com qualquer processo nativo pai ou filho vivo.

```powershell
private/python-env/Scripts/python.exe tools/check_agent_setup.py
private/python-env/Scripts/python.exe -m unittest discover -s tests
./tools/build.ps1 -Target Boot
./tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4
```

Novo manifesto exige tools/lift_spu_overlays.py antes do build. Use SkipLift
somente com gerados atuais; confira instruções e destinos diretos pendentes.
Use tools/run_title_probe.py com ROIs/tempos já revisados e rótulo novo.
Leia logs vivos por trechos limitados de bytes; nunca use Tail contínuo.

## Fontes de verdade

- PROMPT_EXECUCAO_COMPLETA.md: critérios integrais; tasks/todo.md: aceite final.
- SDK a6d76c895f77eb30b90a806c830544e61821b77f e patch reproduzível em patches/.
- .agents/model-routing.md: somente6+, principal e no máximo um auxiliar.
- docs/history/manifest.json: histórico anterior preservado e hashes.
- docs/PORTHEON-reference.md: referência complementar; nada externo executado.
- Substitua este checkpoint ao avançar; não acrescente um diário infinito.
