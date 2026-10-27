# Checkpoint atual — 27/10/2026

Alvo: FIFA Street 2012 PS3 BLUS30882 1.00 → Windows x64 nativo.
Branch: `codex/ps3-native-bootstrap`. Objetivo final: partida offline jogável.
Guia: `docs/AI-HANDOFF.md`; plano: `tasks/plan.md`.

## Estado do produto

**O menu original está estável e o caminho Futsal avança até SELECT TEAM.**
No executável nativo, o fluxo observado foi: título → aviso de autosave →
Hit the Streets → Select Match Type → Futsal → Select Sides → Select Team.
Chicago Fire foi escolhido para o lado esquerdo e apareceu como READY; o
seletor de liga MLS do adversário estava aberto quando o ensaio terminou.
Evidência e hashes: `reports/menu-input-progress.json`.
Run: `private/analysis/runs/1793124900057646500` (480,176 s, timeout).
Capturas revisadas: `private/analysis/pad-neutral-menu-frames/frame_41`,
`frame_47`, `frame_54`, `frame_61`, `frame_68`, `frame_76`, `frame_82`, `frame_88`.

**Ainda não há partida jogável.** Não foram validados adversário, arena,
carregamento da partida, jogadores controláveis, física, áudio ou saída limpa.
O timeout encerrou pai e filho nativos; ausência de block/crash não prova
estabilidade. Blocos pretos/cinzas, diagonais e texto imperfeito persistem.
O indicador da janela mede lotes do backend, não FPS apresentados; no menu e
na seleção houve leituras aproximadamente entre 12 e 22 lotes/s.

## Correção decisiva de input

Sem XInput e com `PAD_NO_KEYBOARD=1`, o port 0 virtual saía de `memset` com
analógicos `0,0`: isso é deflexão máxima para cima/esquerda. O backend também
mantinha eixos antigos depois da desconexão física. `patches/0012` agora
centraliza os quatro eixos em 128 e zera os botões ao desconectar/inicializar.
No ensaio anterior, 25 capturas sem novos comandos percorreram as cinco opções
(24 transições). Após a correção, oito capturas consecutivas mantiveram
Hit the Streets selecionado (zero transições). Um Cross abriu a tela correta;
Down levou de 5-A-SIDE a PANNA RULES e depois a FUTSAL. Isso corrige a falsa
atribuição de navegação aos pulsos nos relatórios anteriores.

## Renderização e desempenho

`patches/0011` transporta `SET_TEXTURE_CONTROL3` para o upload D3D12: layout,
leitura por linha, fingerprint e identidade do cache usam o pitch da textura.
O manifesto agora o registra. Nas capturas atuais, nenhuma textura linear
suportada tinha pitch maior que sua linha compacta; portanto essa correção
não explica nem resolveu os blocos visuais do menu. Investigar RT aliases,
alpha/blend e composição por draw, sem atribuir causa sem reprodução.

O maior engasgo observado na entrada do menu foi compilação de PSOs:
uma janela `[PERF]` consumiu 12,94 s em PSO, com 124 misses. Depois do
carregamento, uma amostra da seleção de time marcou 14,49 lotes/s; 86% do
tempo estava fora de `render_frame`. O ganho de FPS do novo código não foi
medido em cenários equivalentes. `tools/play.ps1` força `PS3_VERBOSE=0` para
evitar a torrente de logs gerada pelo stderr redirecionado.

## Validação do incremento

- `tools/build.ps1 -Target Runtime`: compilou; 20/20 CTest passaram.
- FullGame `/O1` com SPU relinkado após encerrar todos os processos nativos.
- `tools/apply_patches.py`: série autoral 0001–0012 reproduzida e verificada.
- 65/65 jobs de assets amostrados corresponderam; zero eventos
  `[fifa-block]`/`[fifa-crash]`, zero erros de parse no run final.
- Cinco hashes do save original conferidos e inalterados; probes usaram cópias.
- `tools/play.ps1`: sintaxe PowerShell validada; boot/filho abriram e a janela
  foi verificada com `IsWindowVisible=True`. O teste foi parado por taskkill.
- SHA-256 do FullGame atual: `db8525d6e23ccf943708ba9cf593e55fc5b1e63f5669fe16007c65304f83a6b5`.

## Como abrir e próximo trabalho

Execute `Iniciar-FIFA.cmd` na raiz. O perfil interativo fica em
`private/userdata_interactive`; Enter = Start, Z = confirmar, X = voltar,
setas = navegar. A janela precisa ter foco. Logs em `private/analysis/interactive-*`.
Este launcher abre o binário local; ainda não é pacote autônomo distribuível.

1. Selecionar adversário no SELECT TEAM, avançar até venue/arena e seguir o
   próximo bloqueio real com capturas guiadas. Preservar o save original.
2. Reproduzir um bloco visual em draw específico; examinar alias CAB
   (RT 1280×720 amostrado como textura 2560×720), blend/alpha e self-sampling.
3. Medir frames realmente apresentados sem RSX_CAP contínuo; separar o custo
   de compilação inicial de PSO do custo estável do jogo.
4. Validar teclado/controle físico no menu até uma partida offline; depois
   melhorar gráficos, áudio, regras, estabilidade e execução independente.

Histórico anterior de REA/Rizin, SPU e pad: `docs/AI-HANDOFF.md`,
`reports/pad-input-consumer.json` e `reports/menu-renderer-progress.json`.
