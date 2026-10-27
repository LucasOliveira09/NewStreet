# Checkpoint atual — 27/10/2026

Alvo: FIFA Street 2012 PS3 BLUS30882 1.00 → Windows x64 nativo.
Branch: `codex/ps3-native-bootstrap`. Objetivo final: partida offline jogável.
Guia: `docs/AI-HANDOFF.md`. Plano: `tasks/plan.md`.

## Estado do produto

**Menu principal original visível e navegação confirmada no executável nativo.**
Inputs mudaram a seleção; Cross abriu `SIGN IN FAILED`; outro Cross em `OK`
fechou o aviso e retornou ao menu. A captura mostra opções Hit the Streets,
World Tour, Online, My Squad e Practice Arena, com o fundo original do Messi.
Ainda há blocos cinza, diagonais e ícones/texturas incorretos. Não foi validada
entrada em modo offline, arena 3D, partida, estabilidade ou performance.

Evidência: [`menu-renderer-progress.json`](reports/menu-renderer-progress.json).
Run: `private/analysis/runs/1793122289140347600`, 363.708 s.
Capturas em `private/analysis/menu-navigation-depth-exact-frames/`:
- `frame_32`: My Squad selecionado antes dos comandos de navegação.
- `frame_36`: Online selecionado; `frame_46`: Practice Arena selecionado.
- `frame_55`: aviso de login; `frame_67`: retorno ao menu após confirmar OK.

Cross enviado após revisar Practice Arena abriu o aviso de login. Isso não
prova entrada nessa arena; a correspondência exata entre cada pulso de input,
animação e frame apresentado precisa de medição. O ensaio foi encerrado
intencionalmente com `taskkill` após a validação visual (exit 1), sem eventos
`fifa-block`/`fifa-crash`. Não é evidência de encerramento limpo ou estabilidade.

## Correções que recuperaram a interface

- `0005/0006`: root signature e estado cobrem as 16 unidades de textura.
  Atlas, 96 uploads, 16 RTs e dois bancos de descritores por draw não se sobrepõem.
- `0007/0008`: sondas de cor/textura reconhecem o HLSL atual (return e MRT).
  FP_TEX reescreveu FP0x12D041 para amostrar o centro da unidade8; a captura
  final preta não isola o conteúdo dessa textura da composição posterior.
- `0009`: lookup pelo endereço do RT precede heurísticas de dimensão. Antes,
  passes reais liam a cópia do backbuffer em vez de seus produtores offscreen.
- `0010`: enable, máscara de escrita e comparação de profundidade são
  capturados por draw, traduzidos e incluídos na identidade do PSO. O renderer
  anterior forçava depth ligado e escrita em toda a interface.
- Comparação intermediária com `SCREEN_AS_TEX=0` mostrou apenas gradiente
  amarelo; após estado de profundidade correto, o menu original apareceu.

## Validação do incremento

- `tools/build.ps1 -Target Runtime`: build e 20/20 testes passaram.
- `python -m unittest discover -s tests -p test_title_probe.py`: 6/6 passaram.
- `python tools/apply_patches.py`: reconstruiu e conferiu a série 0001–0010.
- FullGame `/O1`, SPU ligado, relinkado após encerrar pai e filho nativos.
  SHA-256 e comandos em `reports/menu-renderer-progress.json`.
- Quatro probes novos: zero PSO FAIL, zero eventos block/crash e 65/65 amostras
  de assets conferidas por ensaio. As amostras não cobrem todos os assets.
- Revisão estática independente dos patches 0009/0010 sem bloqueador novo.
- Os cinco hashes do save original continuam iguais ao checkpoint; cada probe
  usou uma cópia de `private/userdata`, com HDD0/HDD1 explícitos.

## Como abrir

Execute `Iniciar-FIFA.cmd` na raiz. Ele chama `tools/play.ps1`, usa ELF/disco e
executáveis locais e mantém um perfil separado em `private/userdata_interactive`.
Enter = Start; Z = confirmar; X = voltar; setas = navegar. A janela precisa ter
foco para o teclado. O launcher preserva logs em `private/analysis/interactive-*`.
O launcher teve sintaxe PowerShell conferida; o round trip acima foi validado
pelo probe, não por teste manual de teclado. Não é pacote autônomo distribuível.

## Próximo trabalho

1. Entrar em Hit the Streets offline, revisar os frames após cada input e
   capturar o próximo serviço/SPU não implementado ou a seleção de times.
2. Medir atraso/repetição de inputs e verificar teclado e controle físico.
3. Corrigir artefatos com estado por draw: pitch linear, aliases de RT (há
   RT1280×720 lido como textura2560×720), culling/UV/remap e self-sampling.
4. Aposentar recursos recriados/evictados pelo fence da submissão que realmente
   os referencia; `wait_for_gpu()` não protege uma lista ainda não submetida.
5. O default `depth_func=1` do parser não é enum GL; corrigir com regressão se
   esse estado for observado antes de SET_DEPTH_FUNC. Stencil permanece parcial.

REA/Rizin e evidências PPU/SPU anteriores continuam em `docs/AI-HANDOFF.md` e
`reports/pad-input-consumer.json`. Não repetir investigação do consumo básico do
controle como se o menu ainda estivesse bloqueado no logo. Gameplay segue aberto.
