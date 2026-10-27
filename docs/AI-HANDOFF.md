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

No checkpoint desta revisão, o boot mostrou título e aviso de autosave, e
Start/Cross chegaram ao código original em probes anteriores. Perfil local foi
criado e relido. **Menu navegável, seleção, cena 3D, controle de jogadores,
bola, partida e ciclo completo ainda não foram comprovados.** Não descreva o
projeto como jogável. Janela, pedido de flip ou imagem preta não equivalem a
partida. Uma saída por timeout ou código 90 é falha/bloqueio, nunca sucesso.

## Onde estão código, dependências e evidências

- `src/`: runtime nativo, inicialização, processos, gráficos, input, serviços e diagnósticos.
- `tools/`: extração/lifting, build, probes, inspeção e validação de manifests.
- `tests/`: probes nativos e testes Python/C++; use os checks pertinentes ao código alterado.
- `vendor/ps3recomp/`: SDK externo fixado; não commitar alteração solta nesse submódulo.
- `patches/0001-strict-native-boot.patch`: reprodução de mudanças autorais do SDK.
- `toolchain.lock.json`: commits e versões fixadas; confira o checkout antes de atualizar algo.
- `private/`: ISO/ELF/assets, executáveis, gerados, perfis, logs e capturas locais; nunca versionar.
- `reports/native-boot-checkpoint.json`: evidência do último ensaio de boot.
- `reports/performance-opening.json`: medições de abertura, instrumentação, hashes e limitações.
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

## Checkpoint técnico ativo

1. **FPS/espera do RenderThread.** `/O1` é padrão. A comparação de workload
   pareado reporta 8,225 → 8,75 batches/s, mas batches incluem passes offscreen
   e não são FPS visível. Uma medição de abertura separada tem números diferentes
   e não deve ser comparada como pareada. FTrace de abertura registrou 99 pedidos
   de flip em 12 s (mediana 120,6 ms) e drain FIFO RSX de 26,2 ms por intervalo.
   PPU22 (`RenderThread`) registrou 305.628 polls de sleep solicitado de 30 µs
   em 12 s no retorno `0x000A969C`; o estado visto alternou 0/1 e o loop termina
   em valor negativo. Otimização do temporizador foi realmente compilada uma vez,
   não alterou a mediana (8,76 vs 8,75 batches/s) e foi revertida.
2. **Estado do job/asset.** A origem que deve escrever o estado de espera e a
   relação causal com a taxa de flip ainda são desconhecidas. Arquivos
   `genheadtex.big`, `Player_SFX_01.ast`, `TUNA_SFX_BE.ast` e `TUNA_SFX_FE.ast`
   não foram encontrados nos caminhos esperados do disco extraído; impacto no
   estado ou na renderização não foi demonstrado.
3. **Renderização.** Pipeline alcançou criação para shaders de 5.024/5.472 bytes
   no ensaio relatado; uma falha de sampler 4 excede root signature limitada a
   quatro unidades. Há espaços de descritor que se sobrepõem (VP cache 1..96,
   RT 5..20 e base de draw 32). Corrigir o mapeamento real das 16 unidades,
   estado por draw e heaps antes de declarar banco de texturas correto.
4. **Vida útil de recursos.** D3D12 ID 921 indica recurso destruído antes da
   execução do comando e já ocorria no baseline. A aposentadoria precisa seguir
   o fence da submissão efetiva; não aguarde trabalho ainda não enviado.
5. **Captura/jogo.** Última captura posterior a LOADING ficou preta. Várias
   causas continuam possíveis; nenhum vínculo causal foi isolado.

O follow-up mais recente observou PPU stores de `1` pelo endereço guest
`0x000A8E10` (LR `0x000A95DC`) para `0x106E0900`, e requisições SPU4/5 MFC_GET
(`0x40`) / MFC_PUT (`0x20`) cobrindo 8 bytes na mesma EA a partir de LS
`0x3ED10`, PC `0x0156C`. O hook `SPU_WATCHEA` está antes de executar o comando;
ele não revela o valor efetivamente escrito. A amostra read-only de 315 leituras
em ~7,9 s, a cada25 ms, encontrou só0 e1 (nunca negativo); transientes menores
que o intervalo continuam possíveis. O ensaio direto pula EBOOT e foi feito só
para essa leitura; não substitui a execução FullGame normal.

Veja IDs de runs, contagens, hashes e escopo em
[`performance-opening.json`](../reports/performance-opening.json). Preserve a
distinção entre dado observado, hipótese e conclusão. Próximo passo: armar
`PPU_WW_GUARD=1` para atribuir qualquer escrita na página. Se o SPU DMA alterar o
estado, capturar valor e resultado após a execução do MFC por um hook estreito.
Não force status nem burle o wait.

## Próxima investigação recomendada

Siga a prioridade atual em `tasks/plan.md`: identificar o produtor do objeto de
espera associado ao loop observado, sem forçar o estado nem pular o loop. Faça
uma observação nova que registre endereço, valor e thread/PC que escreve, ou
prove que o mecanismo atual não consegue identificar o escritor. Procure primeiro
instrumentação já existente em código, manifests e executáveis locais. Se for
preciso adicionar watchpoint/log, delimite a escrita, documente overhead e remova
instrumentação temporária ou transforme-a em ferramenta suportada. Correlacione
com conclusão de jobs/solicitações de assets e chamadas de flip no mesmo run.

Depois de duas tentativas sem informação nova, reveja hipótese, pontos de
instrumentação e evidência antes de repetir. Não conclua que o sleep é a causa
só por consumir tempo de CPU. Um teste de throughput deve usar mesmos inputs,
cena, duração e instrumentação; registre mediana/dispersão, hash do binário e
limites do que foi medido. Continue então o caminho real até menu e partida.

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
