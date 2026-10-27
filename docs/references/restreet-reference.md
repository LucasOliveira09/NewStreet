# ReStreet como referência para o port nativo

Consultado em 27/10/2026: [samuelit0davila/fifa-street-pc-port](https://github.com/samuelit0davila/fifa-street-pc-port). O projeto chama seu port de ReStreet e reconstrói FIFA Street (2012) para Windows. O README informa que a base é a versão Xbox 360 e que o usuário fornece sua própria ISO; o guia de build mostra `default.xex`, DLLs XEX e o SDK ReXGlue. Nosso alvo continua sendo o FIFA Street PS3 BLUS30882, ELF PPU/SPU e runtime `ps3recomp`. Mesmo nome de jogo não significa binário, API, assets ou código executável intercambiáveis.

## O que vale estudar

- **Build reprodutível:** `docs/BUILDING.md` fixa uma revisão de ReXGlue, aplica um patch de projeto uma vez, extrai a ISO em uma árvore privada e separa geração/compilação dos módulos guest do build do launcher. Para nós, reforça a necessidade de fixar ferramenta e revisão, registrar entradas/outputs e preservar artefatos privados. O nosso equivalente já são `toolchain.lock.json`, `patches/` e os manifests em `private/`.
- **Separação por responsabilidade:** o pipeline documenta o executável principal e o módulo DLC `FootballCompEngzf` como saídas guest próprias, além de runtime gráfico, launcher e instalador. No nosso lado, manter separados EBOOT, FIFAZF, overlays SPU, HLEs, backend D3D12 e ferramentas de diagnóstico torna cada bloqueio mais testável.
- **Renderizadores e paridade:** o README diz que o engine gráfico da versão 2.0 é baseado no port Deck de AnDr3zF e lista D3D12/Vulkan, resolução interna, filtros, AA e limite de FPS. Isso é uma trilha para ler decisões de cache/estado e comparar renderização; não é evidência de que o backend ou os shaders funcionem no RSX/PS3.
- **Instrumentação do usuário final:** `docs/STATUS.md` do projeto separa versão testada, máquina, cenários aprovados e não testados. Podemos usar esse formato para registrar nosso hardware, cena, duração, configuração e limitações em cada medição. A alegação de aproximadamente 400 FPS é reportada pelo próprio README em PC de teste e não é comparável com nossos batches ou flips.
- **Asset tooling:** o repositório contém `Tools/ReStreetAssetScan`; estudar a ideia de scanner e inventário pode ajudar na nossa inspeção de assets. Não reutilizar os resultados como se viessem da ISO de PS3 sem comparar hashes e formatos.
- **Escopo do produto:** ReStreet adicionou launcher, salas e online sobre uma base recompilada. Para o nosso objetivo, online/launcher permanecem posteriores a provar menu, partida offline, controle, renderização, áudio e salvamento no port nativo.

## O que não copiar automaticamente

1. Não importar XEX, DLLs compiladas, shaders, offsets ou patches ReXGlue como dependências do PS3 port. A arquitetura Xbox 360 e a pilha XEX/ReXGlue são diferentes do caminho PPU/SPU/RSX que estamos reconstruindo.
2. Não comparar o claim de FPS de ReStreet diretamente com nosso FTrace. Uma comparação exige mesma cena, resolução, GPU/CPU, backend, limite de FPS e definição de frame.
3. Não adicionar o port como submódulo nem clonar os arquivos do jogo. Primeiro ler o patch/arquitetura como referência e registrar uma hipótese específica para validar no nosso runtime.
4. Antes de portar código, revisar a licença do arquivo exato e seus componentes. O README descreve o MIT como licença de scripts/launcher/instalador originais e deixa claro que isso não dá direito de redistribuir arquivos ou conteúdo FIFA. Este documento registra observações e links; não incorpora código nem assets de ReStreet.

## Próximas leituras do upstream

- [README e visão geral](https://github.com/samuelit0davila/fifa-street-pc-port)
- [Build a partir do código](https://github.com/samuelit0davila/fifa-street-pc-port/blob/main/docs/BUILDING.md)
- [Status e limites de validação](https://github.com/samuelit0davila/fifa-street-pc-port/blob/main/docs/STATUS.md)
- [Changelog](https://github.com/samuelit0davila/fifa-street-pc-port/blob/main/CHANGELOG.md)
- `patches/rexglue-local-changes.patch` e `Tools/ReStreetAssetScan/` para inspeção pontual quando houver uma pergunta concreta sobre codegen ou assets.

**Decisão atual:** manter ReStreet como referência técnica externa, sem dependência de build e sem código importado. Qualquer uso futuro deve apontar para o arquivo/commit consultado, compatibilidade comprovada, licença e uma validação no ELF de PS3.
