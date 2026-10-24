# Plano de continuidade: FIFA Street nativo no Windows

## Escopo

Implementar o port offline de FIFA Street PS3 BLUS30882 01.00 para Windows x64.
O prompt completo, incluindo requisitos e critérios de conclusão, está em
`../PROMPT_EXECUCAO_COMPLETA.md`. Este plano ordena a próxima execução; não relata
integrações ainda inexistentes.

## Base validada anteriormente

Commit `e96e614`: extração dos dois SELF, obtenção dos ELF, loader PPU, duas funções
traduzidas com 20.020 retornos testados e 16 testes do runtime aprovados.
Jogo, boot, gráficos e partida ainda não validados. Reproduzir antes de implementar.

## Decisões

- Reutilizar o repositório existente e a revisão fixada de ps3recomp.
- Manter PS3 como entrada; ReStreet é referência de outra plataforma.
- Manter dados e código derivado do jogo em `private/`.
- Versionar adaptadores próprios, scripts, testes e patches de dependências.
- Avançar por código real executado e estados observáveis do jogo.
- Escolher integrações concretas após ler o runtime; não presumir um backend completo.

## Ordem e critérios

| Etapa | Depende de | Aceite | Verificação |
|---|---|---|---|
| Reproduzir baseline | Arquivos locais e toolchain | Build e testes anteriores reproduzidos | `tools/build.ps1`, hashes e logs |
| Revisar fluxo de boot | Baseline | Entradas, argumentos, módulos e contexto identificados | Evidência de bytes, chamadas e imports |
| Preparar loader nativo | Fluxo de boot | Segmentos, BSS, stack, TLS, TOC e OPD coerentes | Testes de memória e contexto |
| Executar startup PPU | Loader | Caminho real executado com primeiro bloqueio rastreável | Trace de módulo/endereço/chamada |
| Completar serviços do startup | Trace | Caminho necessário sem resultados fabricados | Testes de handlers e novo trace |
| Integrar tarefas SPU alcançadas | Inventário e startup | DMA/canais/resultados e sincronização corretos | Comparação de dados e progresso do jogo |
| Renderizar frame original | Startup e dados | Frame produzido pelo jogo | Captura com cenário e logs de RSX |
| Navegar nos menus | Frame e serviços | UI original responde a entradas | Navegação observada e registrada |
| Completar partida | Menus, SPU, gráficos e entrada | Jogo interativo do início ao fim | Roteiro de partida e registros |
| Validar saves e progressão | Partida | Estado persiste após reiniciar | Gravar, fechar, abrir e retomar |
| Ampliar conteúdo offline | Fluxos básicos | Matriz de modos e conteúdo validada | Cenários por modo/arena/fluxo |
| Medir estabilidade e desempenho | Gameplay | Sem falhas críticas nos cenários medidos | Sessões repetidas, perfis e frametimes |
| Reproduzir instalação | Integrações completas | Checkout limpo e dados locais geram jogo funcional | Build/execução fora da pasta de desenvolvimento |

Cada linha representa uma frente que deve ser dividida em incrementos pequenos
antes de editar. Para cada incremento, identificar arquivos exatos, dependências,
até três critérios de aceite e teste correspondente. Priorizar 1–5 arquivos por
mudança; subsistemas grandes não devem virar um único patch.

## Checkpoints

1. Fundação: baseline, fluxo de boot e primeira inicialização rastreada.
2. Apresentação: primeiro frame e menu reais.
3. Gameplay: primeira partida completa e retomada de save.
4. Cobertura: matriz offline, estabilidade e instalação reproduzível.

Cada checkpoint exige evidências e commit. Somente o quarto, com todos os
requisitos obrigatórios cobertos, permite avaliar a declaração de port completo.

## Riscos concretos

| Risco | Tratamento |
|---|---|
| REA não admite ELF64/PPC64 na versão instalada | Usar ferramentas compatíveis; manter diagnóstico original |
| Contagem de imports confundir nomes com implementação | Auditar biblioteca/NID, ABI, wrappers e comportamento |
| Lifter ou runtime apresentar stubs silenciosos | Diagnóstico explícito e validação do caminho necessário |
| Arquivos ISO de múltiplos extents serem truncados | Preservar todos os extents no extrator completo |
| SPUs ou renderizador exigirem trabalho específico | Descobrir cedo os caminhos alcançados e validar separadamente |
| Mudanças em vendor ficarem fora do histórico | Patch versionado ou fork fixado, aplicado no bootstrap |
| Dependência não documentada do PC do desenvolvedor | Preparação e build testados em checkout limpo |

Não há estimativa confirmada para finalizar o jogo. Bloqueios e decisões futuras
devem ser registrados no `STATUS.md` pelo agente que iniciar a implementação.
