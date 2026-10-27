# Guia de retomada para agentes — FIFA Street nativo

Atualizado em 27/10/2026. Este arquivo é o mapa de entrada para uma nova IA.
Ele não substitui as instruções, o aceite nem os dados privados do jogo.

## Leia nesta ordem

1. [`../AGENTS.md`](../AGENTS.md): limites de segurança, evidência, build e Git.
2. [`../STATUS.md`](../STATUS.md): checkpoint curto; substitua-o ao concluir um incremento.
3. [`../tasks/plan.md`](../tasks/plan.md): próxima etapa ativa e marcos do produto.
4. [`../PROMPT_EXECUCAO_COMPLETA.md`](../PROMPT_EXECUCAO_COMPLETA.md): objetivo integral e aceite final.
5. O relatório indicado pela etapa e o código específico que será alterado.

Não carregue todo `docs/history/`, `private/`, os arquivos gerados ou o prompt
integral em toda sessão. Consulte o índice de [`history`](history/README.md) e
busque apenas o assunto necessário. `private/` contém entradas e evidências
derivadas do disco local; ele é ignorado pelo Git por projeto.

## Objetivo e critério de verdade

Reconstruir FIFA Street 2012 PS3 BLUS30882 1.00 como aplicação Windows x64
nativa, sem RPCS3/Xenia e sem trocar silenciosamente a recompilação por
interpretador/JIT. O usuário autorizou continuar até alcançar partida jogável.
O aceite completo está no prompt de execução; os próximos marcos estão no plano.

No checkpoint desta revisão, o executável nativo mostra o logo FIFA STREET em
1280×720. START/CROSS/DOWN foram escritos em relatórios válidos; o caller
`0x014351D0` lê o comprimento e o word de botões do buffer local. A imagem não
muda, então a leitura do input está provada, mas mapeamento da ação/transição de
UI não. Perfil de probe foi copiado e os saves originais foram preservados.
**Menu navegável, seleção, cena 3D, controle de jogadores, bola e partida não estão comprovados.** Não descreva o
projeto como jogável. Janela, pedido de flip ou imagem preta não equivalem a
partida. Uma saída por timeout ou código 90 é falha/bloqueio, nunca sucesso.

## Onde estão código, dependências e evidências

- `src/`: runtime nativo, inicialização, processos, gráficos, input, serviços e diagnósticos.
- `tools/`: extração/lifting, build, probes, inspeção e validação de manifests.
- `tests/`: probes nativos e testes Python/C++; use os checks pertinentes ao código alterado.
- `vendor/ps3recomp/`: SDK externo fixado; não commitar alteração solta nesse submódulo.
- `patches/0001-strict-native-boot.patch` e `patches/0002`–`0004`: reprodução dos patches autorais do SDK.
- `toolchain.lock.json`: commits e versões fixadas; confira o checkout antes de atualizar algo.
- `private/`: ISO/ELF/assets, executáveis, gerados, perfis, logs e capturas locais; nunca versionar.
- `reports/native-boot-checkpoint.json`: evidência do último ensaio de boot.
- `reports/performance-opening.json`: medições anteriores de abertura.
- `reports/spu-handshake-timing.json`: relógio correlacionado de status PPU, DMA SPU e flips.
- `reports/title-navigation-probe.json`: pacotes válidos sem transição visual.
- `reports/pad-input-consumer.json`: caller `cellPadGetData` e início do parser guest.
- [`references/restreet-reference.md`](references/restreet-reference.md): projeto ReStreet como referência, com limites PS3/Xbox 360.
- `reports/rpcs3-local-reference.json`: configuração observada do RPCS3 local, gravação de referência e procedimento para capturar a navegação após Start.
- [`recomp-ports-reference.md`](recomp-ports-reference.md): comparação de ReStreet e ports PS3 em `ps3recomp`, com implicações para SPURS/render.
- `docs/history/`: checkpoints antigos preservados; podem estar desatualizados.

Os identificadores de guest como `0x000A969C` são endereços observados, não
nomes semânticos. Contagens de funções, wrappers ou registros SPU não provam
que os serviços ou algoritmos estejam completos. Para associar uma rotina SPU,
registre bytes/faixa/hash e evidência da entrada observada; preserve limites de
código, constantes, stops e PCs de retorno.

## Como reproduzir build e observação

O script de build valida o commit do submódulo, reaplica o patch versionado,
usa Visual Studio x64, LLVM privado e CMake/Ninja do Visual Studio. As entradas
privadas da toolchain e do jogo precisam existir localmente.

```powershell
Set-Location D:\Ludevi\projetos\fifa-street-native
git status --short
git branch --show-current
git rev-parse HEAD
private\python-env\Scripts\python.exe tools\check_agent_setup.py
./tools/build.ps1 -Target Boot
./tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4
```

`-SkipLift` só é válido quando os arquivos gerados correspondem às entradas e
ao manifesto atuais; caso contrário, faça lifting. O manifesto SPU deve estar
atualizado antes de FullGame. Para diagnóstico sem otimização, use
`-DebugFullGame`; FullGame usa `/O1` por padrão. O resultado em
`private/build/fifazf_full/` é o binário da sessão de desenvolvimento, ainda
dependente dos ELF/disco conforme os argumentos de runtime; não é instalador
autônomo pronto para distribuição.

`tools/run_native.py` produz um probe controlado (`--profile startup|full`,
`--timeout`, `--direct`, rastreio/captura/observação de assets). Para uma ação
de botão condicionada por tela, use `tools/run_title_probe.py`: referências de
captura devem ser inspecionadas previamente e cada entrada deve ser autorizada
por uma tela/ROI revisada. Um botão enviado não prova que o jogo o aceitou;
inspecione o estado seguinte e os artefatos do run. Nunca reaproveite um label
como se fosse nova evidência.

Antes de relink ou iniciar outra execução, confira que o processo nativo e seus
filhos encerraram. Não basta o launcher sair. Ao ler log vivo, leia intervalos
limitados de bytes; não use `Get-Content -Tail` em stderr aberto. Não substitua
o perfil de save para facilitar probes: compare os cinco hashes do checkpoint.
Probes diretos precisam definir `PS3_HDD0_ROOT` e `PS3_HDD1_ROOT` para
`private/userdata/dev_hdd0` e `private/userdata/dev_hdd1`; o lançamento de memória
registrado abaixo omitiu essas variáveis e criou `gamedata/trophies/` na raiz.
Esse conteúdo foi mantido e a pasta está ignorada pelo Git.

### Referência externa no RPCS3

O RPCS3 portátil local usa Vulkan e XInput e carrega BLUS30882 por ISO. A gravação
disponível termina no título `PRESS START BUTTON`; ela não registra navegação.
Para comparar o comportamento original, siga o procedimento em
[`rpcs3-local-reference.json`](../reports/rpcs3-local-reference.json). O RPCS3
serve como referência do original, não como evidência de avanço do port nativo.
Na execução informada em 27/10, o usuário chegou a uma partida; a biblioteca
depois mostrou última execução 09:49 e 22min55s acumulados. A inspeção da tela
09:51 já encontrou a biblioteca, sem nova gravação/captura ou log. Trate a
entrada em partida como relato do usuário até haver evidência visual; não use o
rótulo geral `Ingame` da lista de compatibilidade como prova desta execução.

Uma captura posterior confirmou o boot até a cena offline Arsenal × Chicago Fire,
com HUD e 3D visíveis. A captura é `private/analysis/rpcs3_reference/live-match-current.png`;
detalhes e limites estão no relatório estruturado e no documento de referências.

### REA

O setup REA aprovado está instalado; esta sessão usou REA CLI 6.7.0 com Rizin
0.9.1. O MCP `open_binary` não aceita o ELF PowerPC, mas `execute-rizin-command`
funciona quando o processo define `REA_RIZIN_COMMAND` para o `rizin.exe` privado
e inclui seu diretório `bin` no PATH. O comando por endereço no callsite de input
retornou Evidence `ev_78025d4611a3c21b91bab08e45f2a20d2c04ce0b6ba216780d61937298af555`.

O ELF reporta headers de programa malformados; os offsets e instruções pontuais
são observações, mas não confie nos limites de função/símbolos automáticos. REA
anteriormente analisou `func_000A71E4` (wait de 30 µs até estado zero),
`func_000A8E10` e o MFC em `sportsrna_spupatch`. Rizin não decodifica SPU aqui;
use lifter e correlação de bytes/hash/runtime para SPU.

## Checkpoint técnico ativo

1. **Input e navegação.** Run `1793112938625277900` usou cópia do perfil e
   `PAD_ALWAYS_CHANGE=1`, `PAD_REPORT_TRACE=1`, `PAD_SCRIPT='4:0x0008,7:0x4000,10:0x0040'`.
   Seis transições válidas (`len=20`, `mode=122`) foram escritas em
   `0xD0189CE0`; oito capturas tiveram o mesmo hash e mostram o logo. Follow-up
   `1793113545266437400` e REA identificam NID `0x8B72CDA1`, LR `0x014351D0`;
   o guest lê `len` e o word de botões no buffer stack-local e chama helper
   `0x01434DB8`. Isso prova que o parser do guest recebe o relatório, não que a
   ação seja mapeada à troca de tela. Evidência em
   [`pad-input-consumer.json`](../reports/pad-input-consumer.json) e
   [`title-navigation-probe.json`](../reports/title-navigation-probe.json).
2. **Handshaking e flips.** Run direto `1793111736649624200`, trace de 12 s:
   472 pedidos de flip, mediana 15.8 ms (63.2 solicitações/s, não FPS visível),
   237 stores de status 1 e 236 MFC GET/PUT de status. Correlação aproximada por
   ordem encontrou 236 ciclos; não há ID do job e causalidade não está provada.
   Ver [`spu-handshake-timing.json`](../reports/spu-handshake-timing.json).
3. **Identidade do MFC.** `wrch MFC_Cmd` em `sportsrna_spupatch`, PC `0x015DC`,
   bytes `21 A0 0A 8B`, overlay residente ID `592606456`; GET retorna por LR
   `0x1408`, PUT por `0x14F0`. O contexto SPU `526190333` não é ID do overlay.
   O significado do job superior permanece desconhecido.
4. **Desempenho.** `/O1` é padrão. Medição pareada anterior foi 8.225 → 8.75
   batches/s; são batches incluindo passes offscreen, não FPS. A alteração de
   timer não teve ganho e foi revertida.
5. **Renderização.** Sampler 4 excede root signature limitada a quatro unidades;
   bancos de descritores ainda se sobrepõem. D3D12 ID 921 indica recurso
   destruído antes de Execute; aposentar pelo fence efetivamente submetido.
   Uma captura após LOADING ficou preta; causa não isolada.

`func_000A71E4` faz poll de 30 µs e sai quando o word em `*(objeto+0xC)` é zero.
`func_000A8E10` publica 1 em `0x106E0900`; o SPU lê 1 e grava 0. Preservar o
handshake/wait até provar semântica superior. Não repetir `PPU_WW_GUARD=1`:
armou cedo e gerou 73.845 eventos na página de 4 KiB. Use watch estreito.

O conjunto versionado de patches vai até `0004-ppu-status-watch-timestamp.patch`. `tools/run_native.py` usa `setdefault` para `PS3_HLE_TRACE`, então o chamador pode aumentar o trace sem editar o script.
`python tools/apply_patches.py` reconheceu 0001–0004 aplicados. O gate
`tools/build.ps1 -Target Boot` ficou preso em `check_switch_lowering.py` e foi
cancelado; ele não foi aprovado nesta revisão. CMake direto reconstruiu o target
`fifa_boot`, os 48 testes `test_boot_diagnostics.py` passaram, e o relink
`tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4` concluiu. SHA-256
do FullGame: `C9D2CBA494E2B47D44B5339728AB50A3E6FF6927D7DB69EF9B8EFE6002A6C99D`.

### Próxima investigação recomendada

1. Seguir a rotina caller iniciada em `0x014351D0`. O callsite `0x014351CC`
   fornece `SP+0x70` a `cellPadGetData`; após retorno verifica `len`, lê o word
   em `SP+0x78` e chama `0x01434DB8`. Use REA/Rizin por endereço e identifique os
   bits/eventos e o estado destino; não atribua nome sem evidência.
2. Correlacionar a rotina com `cellPadSetPortSetting` (0x4 e 0x2 observados),
   `mode=122`, tamanho/offsets do report e o fluxo de UI. Não mudar semântica até
   descobrir por que o branch de ação não muda o título.
3. Repetir entrada e capturar a próxima tela. Aceite é transição reproduzível,
   não só escrita/leitura de um pacote.
4. Depois voltar aos bloqueios de renderização e alcançar uma partida offline.

O repositório [ReStreet](https://github.com/samuelit0davila/fifa-street-pc-port)
serve como inspiração de pipeline e produto, mas recompila XEX de Xbox 360 via
ReXGlue. Não reutilize binários/patches como dependências do port PS3. Consulte
[`references/restreet-reference.md`](references/restreet-reference.md) antes
de uma comparação concreta. Rizin não interpreta SPU; preserve bytes, faixa,
hash, PC e logs runtime.

## Registrar cada incremento para a próxima IA

Ao fechar um incremento técnico:

1. Relacione a pergunta, hipótese e evidência anterior que justificaram a mudança.
2. Registre arquivos/código alterados, comando exato e configuração/hash do build.
3. Guarde logs, capturas, JSON e dumps grandes em `private/`; versione apenas
   scripts, manifests e relatórios sem material proprietário.
4. Marque o resultado como confirmado, rejeitado ou inconclusivo; cite limitações.
5. Atualize `STATUS.md` (60–100 linhas, estado atual) e o item ativo do plano.
   Use `reports/` para resultados estruturados; não transforme STATUS em diário.
6. Revise `git diff`, faça os checks pertinentes, `git diff --cached --check`,
   adicione caminhos explícitos e crie commit local pequeno. Não publique remoto.
7. Deixe o próximo passo executável, incluindo arquivos/funções e critério de
   parada/aceite. Se a hipótese mudar, documente o porquê e mantenha dados antigos.

## Não fazer

- Não preencher retornos de serviço, status CELL ou resultados para passar boot.
- Não apagar ou sobrescrever saves privados; não commitar código/ativos derivados.
- Não chamar um teste unitário de rotina de prova de algoritmo completo.
- Não afirmar compatibilidade ampla por um único boot, menu ou cena sintética.
- Não alterar SDK sem patch reproduzível e validação correspondente.
- Não commitar até conferir os arquivos staged e as alterações preexistentes.
