# Checkpoint atual — 27/10/2026

Alvo: FIFA Street 2012 PS3 BLUS30882 1.00 → Windows x64 nativo.
Branch: `codex/ps3-native-bootstrap`. Objetivo final: uma partida offline jogável.
Guia de retomada: `docs/AI-HANDOFF.md`. Plano: `tasks/plan.md`.

## Estado do produto

O executável nativo abre em D3D12 na RX 580 e mostra o logo FIFA STREET em
1280×720. Uma captura válida confirma renderização do título, mas nenhuma das
entradas recentes abriu menu. Não há menu navegável, seleção de modo/time, cena
nativa de partida ou partida jogável comprovada. A captura de Arsenal × Chicago
Fire via RPCS3 é só referência do original, não avanço do port.

O probe `1793112938625277900` enviou START/CROSS/DOWN e registrou seis
transições válidas (`len=20`, `mode=122`) no buffer guest `0xD0189CE0`; oito
capturas tiveram hash idêntico e mantiveram o logo. Um follow-up com
`PS3_HLE_ARGS=8B72CDA1` correlacionou o NID de `cellPadGetData` ao LR guest
`0x014351D0`. REA/Rizin mostra o callsite em `0x014351CC`, que passa um buffer
local `SP+0x70`; depois o guest lê `len` e, se não for zero, acessa o word de
botões em `SP+0x78` e chama `0x01434DB8`. A entrada chega ao parser guest, mas
não há transição visual: o logo continuou idêntico. O significado dos bits e o
estado/UI chamados depois ainda precisam de análise. `PAD_ALWAYS_CHANGE=1` foi
só diagnóstico e altera a cadência. Timeout não é sucesso. Relatórios:
[`title-navigation-probe.json`](reports/title-navigation-probe.json) e
[`pad-input-consumer.json`](reports/pad-input-consumer.json).

Os cinco arquivos do save original ainda coincidem com os hashes do checkpoint.
Esse probe usou uma cópia em `private/userdata_probe_1793112100000000000`; não
apontou o jogo ao perfil original.

## Próxima pergunta técnica

Seguir `0x01434DB8` e as referências do callsite `0x014351D0` para descobrir
qual estado/evento do jogo recebe cada bit. Confrontar `mode=122`, tamanho e
offsets do `CellPadData` com a rotina guest; preservar o input realista e não
injetar estado interno. Só mudar o HLE depois de uma incompatibilidade provada.

REA MCP `open_binary` rejeita este ELF PowerPC como arquitetura não suportada.
O REA CLI 6.7.0 com Rizin 0.9.1 funciona ao definir `REA_RIZIN_COMMAND` e
acrescentar o diretório `bin` privado ao PATH do processo. O comando PPU local
produziu Evidence `ev_78025d4611a3c21b91bab08e45f2a20d2c04ce0b6ba216780d61937298af555`.
Rizin avisa que há program headers malformados; interpretar só as instruções por
endereço e não confiar em limites de funções/símbolos automáticos. Rizin não
decodifica SPU neste ambiente; atribuições SPU usam lifter e trace bytes/hash.

## Wait PPU/SPU e flip timing

A evidência do REA/Rizin no ELF (`func_000A71E4`) diz que o wait de 30 µs sai
quando o word em `*(objeto+0xC)` é zero. O PPU publica 1 em `0x106E0900` por
`func_000A8E10` / LR `0x000A95DC`; o SPU faz GET de 1 e PUT de 0. A finalidade
do job superior e o efeito no renderer continuam sem prova.

O probe direto `1793111736649624200` registrou, na janela FTrace de 12 s,
472 pedidos de flip (mediana 15.8 ms; 63.2 pedidos/s, não FPS exibido), 237
stores de status 1 e 236 GET + 236 PUT bem-sucedidos. Correlação por evento mais
próximo produziu 236 ciclos candidatos: mediana status→GET 19.952 ms e GET→PUT
3.719 ms. Não existe job ID para garantir que cada par seja o mesmo trabalho.
Não atribuir causalidade. Relatório: [`spu-handshake-timing.json`](reports/spu-handshake-timing.json).

A proveniência do MFC está corrigida: `0x015DC`, bytes `21 A0 0A 8B`, pertence
ao overlay residente `sportsrna_spupatch`, ID `592606456`, hash
`35274f8f…22aeeae`; GET LR `0x1408`, PUT LR `0x14F0`. `526190333` é ID de
contexto SPU, não identidade do overlay.

## Instrumentação e validação recentes

- `patches/0002-post-transfer-spu-watch.patch` registra EA/bytes/PC/residência e
  tempo FTrace após DMA; `0003` passa o PC guest do `wrch MFC_Cmd`;
  `0004` acrescenta o mesmo relógio às escritas `PPU_WWATCH`.
- `python tools/apply_patches.py` reconhece os patches 0001–0004 aplicados.
- `tools/run_native.py` agora preserva um `PS3_HLE_TRACE` fornecido pelo chamador;
  run `1793113457141600800` pediu 12.000 e reteve exatamente 12.000 HLE events.
- O gate `tools/build.ps1 -Target Boot` ficou preso em `check_switch_lowering.py`
  durante a compilação de fixture; foi cancelado. Não contar esse gate como aprovado.
- CMake direto recompilou `fifa_boot` no build Boot. Os 48 testes de
  `test_boot_diagnostics.py` passaram. `tools/build.ps1 -Target FullGame
  -SkipLift -WithSpu -Jobs 4` relinkou o jogo; SHA-256
  `C9D2CBA494E2B47D44B5339728AB50A3E6FF6927D7DB69EF9B8EFE6002A6C99D`.
- Não foram alterados nem commitados arquivos do submódulo. Patches de SDK são
  versionados somente em `patches/` na raiz.

## Referência ReStreet

O port [ReStreet](https://github.com/samuelit0davila/fifa-street-pc-port) é
uma referência de build, separação de módulos, renderers e validação de produto.
Ele recompila a versão Xbox 360 por ReXGlue; não misturar XEX/patches/backends
com o nosso target PS3 PPU/SPU/RSX. Critérios de reaproveitamento e links em
[`docs/references/restreet-reference.md`](docs/references/restreet-reference.md).
Nenhum código do ReStreet foi importado.

## Outros bloqueios do port

- Benchmark pareado `/O1`: 8.225 → 8.75 batches/s; batches incluem passes
  offscreen e não são FPS. Ajuste de timer sem ganho foi revertido.
- Renderer: sampler 4 fora da root signature; bancos de descritores ainda se
  sobrepõem e precisam mapear 16 unidades reais.
- D3D12 ID 921 mostra recurso destruído antes de Execute; aposentar após fence
  da submissão efetiva.
- Uma captura após LOADING ficou preta. As causas não foram isoladas.
- RPCS3 capturou Arsenal × Chicago Fire, HUD e quadra; movimento, controles,
  desempenho sustentado e partida completa continuam sem gravação verificável.

## Regras para continuar

Preservar saves e comparar os cinco hashes do checkpoint. Probes diretos devem
usar raízes HDD0/HDD1 explicitamente. Timeout, janela aberta, flip ou logo não
são sucesso. Guardar binários, dumps e capturas privadas em `private/`; não
versionar conteúdo derivado do jogo. Antes de relink/probe, confirmar que pais e
filhos terminaram. Rodar só os checks afetados e revisar staged files antes do
commit. O caminho seguinte é provar consumo do input guest, obter navegação real,
então atacar renderização, cena, física, controle, áudio e ciclo de partida.
