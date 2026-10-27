# Plano ativo do port

Estado/evidência: [checkpoint](../STATUS.md) e
[relatório do menu](../reports/menu-renderer-progress.json).
Aceite completo: [prompt](../PROMPT_EXECUCAO_COMPLETA.md).

## 1. Marco concluído: menu original navegável

- Banco completo de 16 texturas, root signature e descritores sem sobreposição.
- Lookup exato de RT antes dos fallbacks por dimensão.
- Estado de profundidade guest por draw e por PSO; 20 testes runtime passaram.
- Start no título → Cross no aviso de save → menu principal original.
- Mudança de seleção, abertura de SIGN IN FAILED e confirmação de OK com retorno.
- Capturas32/36/46/55/67 do run `1793122289140347600` foram revisadas.
- O processo foi encerrado intencionalmente após o ensaio; exit1 não é clean exit.
- Há artefatos visuais. Não há partida ou arena 3D nativa validada.

## 2. Prioridade ativa: alcançar seleção/cena offline

1. Usar perfil copiado e entrada guiada por captura revisada. Não sobrescrever
   os cinco arquivos do save original. `Iniciar-FIFA.cmd` usa perfil interativo separado.
2. Selecionar Hit the Streets offline, aguardar apresentação após cada comando
   e registrar botão/horário/captura anterior e seguinte. Não inferir modo carregado
   a partir do highlight: o Cross após Practice Arena exibiu um aviso de login.
3. Validar também teclado (setas, Z/X, Enter) e controle físico; medir latência e
   repetição. Os pulsos PAD_FILE do ensaio ainda não têm medição um-a-um.
4. Ao aparecer um block/crash, seguir endereço/bytes/PC com REA/Rizin/lifter e
   implementar semântica real. Preservar saída90 e diagnóstico de faltas.
5. Aceite seguinte: seleção de times/cena e jogadores/bola visíveis; depois
   controle, animação, física, áudio e regras verificadas em uma partida offline.

## 3. Renderização e recursos ainda abertos

- Artefatos cinza/diagonais/ícones; reproduzir em um draw identificável.
- Registrar formato/pitch guest e control3 para aliases: CAB é RT1280×720,
  mas op006 lê o mesmo raw como textura2560×720. Não adivinhar conversão.
- Upload de textura linear não preserva pitch guest; separar largura de stride.
- Resolver self-sampling com semântica explícita; não usar uma cópia de tela arbitrária.
- Recriação/evicção de RT/textura durante prepass pode liberar recurso referenciado
  por lista ainda não submetida. Corrigir retirement, sem esperar fence não enviado.
- Default depth_func1 do parser não é GL0x201; fallback atual mantém LEQUAL até
  SET_DEPTH_FUNC. Stencil, alpha test e scissor guest exigem cobertura futura.

## 4. Build e encerramento de incrementos

- SDK fixado; mudanças reproduzíveis na série `patches/0001`–`0010`.
- Runtime: `tools/build.ps1 -Target Runtime`; copiar a lib de runtime-clang para
  `private/build/boot/sdk/ps3recomp_runtime.lib` antes de FullGame.
- Jogo: `tools/build.ps1 -Target FullGame -SkipLift -WithSpu` apenas quando os
  gerados e manifesto já estão atualizados. Nunca relinkar com pai/filho vivos.
- `apply_patches.py` compara o resultado completo reconstruído quando patches
  posteriores invalidam o reverse-check individual de um patch anterior.
- Checks proporcionais, revisão de diff, relatório, STATUS/handoff e commit local
  com caminhos explícitos e `git diff --cached --check`. Não publicar remoto.

## 5. Evidência anterior preservada

- Consumo de controle PPU, metadados lógicos e REA:
  `reports/pad-input-consumer.json`; agora há navegação visual comprovada.
- Handshake PPU/SPU e flips: `reports/spu-handshake-timing.json`; flip não é FPS.
- SPU: identificação por bytes/faixa/hash, CRT e entradas reais de workloads
  já traduzidos permanecem no checkpoint/histórico. Não refazer a análise inteira.
- ReStreet recompila Xbox360/XEX; serve como referência, não como dependência PS3.
- Próximos marcos: partida completa → pausa/retorno → save/retomada → estabilidade
  e performance → execução reproduzível fora da pasta de desenvolvimento.
