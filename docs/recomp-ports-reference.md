# Referências de ports por recompilação

Consulta em 27/10/2026 para orientar o port nativo de FIFA Street PS3. Repositórios
de terceiros são referências de método e comportamento; não importar código ou
ativos sem validar licença, arquitetura, versão e evidência.

## FIFA Street no PC

- [ReStreet](https://github.com/samuelit0davila/fifa-street-pc-port) recompila a
  versão de Xbox 360 de FIFA Street 2012, com renderer D3D12/Vulkan, launcher e
  online comunitário. É a referência mais próxima de produto e jogabilidade.
- A build Xbox 360 não é o ELF PS3 deste projeto: CPU, ABI, sistema operacional,
  formato dos módulos e execução de jobs são diferentes. Não reutilizar o código
  recompilado como se fosse PPU/SPU PS3. Usar ReStreet para comparar fluxo,
  apresentação, modos e possíveis requisitos online; validar cada detalhe na
  versão PS3 via RPCS3.

## Ports PS3 com o mesmo toolkit

- [ps3recomp](https://github.com/sp00nznet/ps3recomp) é a base de recompilação
  estática que já usamos: PPU/SPU para C/C++ mais runtime HLE e renderer RSX.
  O próprio projeto deixa claro que build e testes de runtime não provam que um
  jogo executou; o estado da linha de jogos em execução é a evidência separada.
- [inFAMOUSreborn](https://github.com/whompay/inFAMOUSreborn) mostra um port
  Windows que recompila PPU e SPU e mantém build/regeneração por cópia local do
  jogo. Comparar o pipeline e cobertura antes de copiar ajustes de runtime.
- [Folklore PS3](https://github.com/Mava-b/folklore-decomp) chegou a gameplay
  nativo e implementa o sistema de jobs SPURS. Consultar especialmente o design
  de filas, eventos e conclusão de jobs para nossa investigação do wait; os
  protocolos do jogo continuam específicos.
- [Twisted Metal PS3](https://github.com/sp00nznet/twistedmetal) é uma comparação
  de engine útil: código real atinge menus, instalação de dados, HUD e caminho
  de draw no D3D12. O projeto relata que capturas entre flips/limpezas do frame
  pareciam vazias; sincronização da captura com o flip deve ser auditada no nosso
  black frame, sem assumir que essa seja a causa aqui.

## Evidência original disponível para este port

O RPCS3 local, build exibida `0.0.43-20402`, alcançou uma cena offline de
Arsenal × Chicago Fire, 0–0, relógio visual 2:00, com quadra, jogadores, bola e
HUD. A captura está em `private/analysis/rpcs3_reference/live-match-current.png`.
Ela prova que a versão PS3 chegou a renderizar a cena; não prova movimento,
resposta ao controle, FPS sustentado ou partida completa. O fluxo observado foi
autosave → Select Sides → Select Team → partida. O RPCS3 retornou à biblioteca
logo após a captura; causa desconhecida, logs vazios.

## Aplicação ao próximo incremento

1. Usar a tela/partida RPCS3 acima como baseline visual versionado apenas por
   metadados; manter a imagem dentro de `private/`.
2. Continuar identificando o produtor do estado terminal do objeto de wait, sem
   falsificar status nem pular o laço.
3. Para a captura preta, comparar o instante do flip do guest, o clear seguinte,
   o fence submetido e o frame efetivamente capturado. O relato de Twisted Metal
   torna essa uma hipótese de observação, não uma correção presumida.
4. Integrar achados de SPURS/render somente quando as entradas, semântica e
   diferenças de versão estiverem demonstradas para FIFA Street.
