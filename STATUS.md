# Checkpoint atual — 28/10/2026

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
No binário do ensaio anterior, o indicador da janela contava lotes do backend,
inclusive os que não chamavam Present. `patches/0013` corrige essa contagem;
um novo ensaio no menu mediu 22,00 chamadas a Present/s de mediana em 32
amostras sem captura, após o carregamento. Isso ainda não é FPS de gameplay.

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
tempo estava fora de `render_frame`. Um novo ensaio no menu, após apenas 45
capturas iniciais, mediu 12 títulos de janela: mediana 22,00 lotes/s, faixa
20,70–23,00. As últimas 30 amostras `[PERF]` deram mediana 21,94 lotes/s,
82% do tempo fora de `render_frame`, 18% no renderer e zero misses de PSO.
No binário corrigido, as últimas 30 amostras internas marcaram 21,69 lotes/s,
82% fora do renderer, 18% nele e zero misses. Nenhum ganho de FPS está
demonstrado. Detalhes: `reports/menu-performance-clean.json`. A coleta de
pilhas ETW foi recusada pela política do Windows; seis threads saturadas
continuam sem função mapeada. `tools/play.ps1` força `PS3_VERBOSE=0` para
evitar logs excessivos.

## Validação do incremento

- `tools/build.ps1 -Target Runtime`: compilou; 20/20 CTest passaram.
- `tools/apply_patches.py`: série autoral 0001–0013 reproduzida e verificada.
- `tools/run_title_probe.py`: contagem/intervalo de capturas configuráveis;
  seis testes Python passaram. `patches/0013` renomeia `[PERF]` para lotes/s
  e conta no título apenas lotes que chamam Present.
- FullGame `/O1` com SPU relinkado após `patches/0013`; novo run de 450,53 s
  chegou ao menu, 65/65 assets iguais, sem block/crash ou erro de parse.
  Terminou por timeout, não saída limpa. Cinco hashes do save original iguais.
- `tools/play.ps1`: sintaxe PowerShell validada; boot/filho abriram e a janela
  foi verificada com `IsWindowVisible=True`. O teste foi parado por taskkill.
- SHA-256 do FullGame atual: `72107eba86d4dba78e9f8ff418a6411696f2dea6356f0d00978ec8c344c979da`.

## Como abrir e próximo trabalho

Execute `Iniciar-FIFA.cmd` na raiz. O perfil interativo fica em
`private/userdata_interactive`; Enter = Start, Z = confirmar, X = voltar,
setas = navegar. A janela precisa ter foco. Logs em `private/analysis/interactive-*`.
Este launcher abre o binário local; ainda não é pacote autônomo distribuível.

1. Selecionar adversário no SELECT TEAM, avançar até venue/arena e seguir o
   próximo bloqueio real com capturas guiadas. Preservar o save original.
2. Reproduzir um bloco visual em draw específico; examinar alias CAB
   (RT 1280×720 amostrado como textura 2560×720), blend/alpha e self-sampling.
3. Mapear as threads saturadas antes de alterar a política de espera/SPU.
   O ETW do Windows recusou a gravação nesta sessão; usar instrumentação local
   pontual ou perfilador com permissão de system performance.
4. Validar teclado/controle físico no menu até uma partida offline; depois
   melhorar gráficos, áudio, regras, estabilidade e execução independente.

Histórico anterior de REA/Rizin, SPU e pad: `docs/AI-HANDOFF.md`,
`reports/pad-input-consumer.json` e `reports/menu-renderer-progress.json`.
