# Checklist do port

Histórico de referência: `e96e614`. Os itens marcados abaixo descrevem somente o
baseline registrado; reproduzi-los no início da próxima sessão.

## Baseline registrado

- [x] Repositório técnico próprio iniciado.
- [x] SELF identificados, copiados e verificados por hash.
- [x] ELF obtidos e abertos pelo loader PPU.
- [x] REA executado e recusa PPC64 registrada.
- [x] Duas funções reais compiladas para Windows x64.
- [x] 20.020 retornos inteiros aprovados contra oráculo matemático.
- [x] Runtime compilado e 16 testes CTest aprovados.

## Próxima sessão

- [x] Ler instruções aplicáveis e conferir branch/HEAD/mudanças existentes.
- [x] Reproduzir baseline e registrar hardware e configuração.
- [x] Revisar EBOOT/FIFAZF, contexto de entrada e dependências iniciais do startup.
- [x] Dividir a integração de boot em tarefas pequenas com arquivos e aceite.
- [x] Executar inicialização real da PPU e registrar o primeiro bloqueio.
- [x] Preservar argumentos e executar troca nativa EBOOT -> FIFAZF.
- [x] Exercitar fronteiras sem suporte e transporte de argumentos em testes.
- [ ] Validar a cobertura ampliada do FIFAZF e resolver o próximo bloqueio.
- [x] Commitar os incrementos validados e atualizar `STATUS.md`.
- [x] Registrar exports reais de sys_libc, sys_libm e sys_libstdcxx.
- [x] Validar um switch PowerPC recompilado e seu retorno compartilhado.
- [x] Validar a correção do switch no caminho real de inicialização.
- [x] Alcançar inicialização GCM com command buffer e região IO reais.
- [x] Inicializar D3D12 no hardware local e consumir a fila RSX do jogo.
- [x] Observar leitura real de locale.big e threads de carregamento.
- [x] Bloquear programa/salto SPU ausente antes de fallback ou interpretação.
- [x] Recompilar e ligar a primeira imagem SPU multi-segmento solicitada.
- [x] Validar handlers de grupos SPU com números não contíguos em teste Windows.
- [x] Confirmar seis threads SPU distintas no carregamento real do jogo.
- [x] Recusar programa SPU desconhecido antes de lookup por entrada compartilhada.
- [x] Testar stops, saída real e retorno indevido de threads SPU sem conclusão fictícia.
- [x] Fechar a descoberta de blocos PPU após mudanças nas fronteiras das funções.
- [x] Identificar e ligar as tarefas raw zlib e SportsRNA patch alcançadas no boot.
- [x] Validar conteúdo/base e distinguir dados mutáveis de instruções de overlays.
- [x] Comparar 47 saídas nativas RefPack/DEFLATE com oráculos independentes.
- [x] Interromper chamadas PPU nulas com diagnóstico completo.
- [ ] Investigar o objeto/chamada em LR `0x11a9f50`.
- [x] Unificar mounts de Open/Write/Rename e testar o ciclo real de arquivos.
- [ ] Confirmar finalização do cache do jogo após resolver o bloqueio de input.
- [x] Validar saídas de tarefas AssetStream concluídas, sem bypass.
- [x] Ligar callbacks dos serviços HLE ao dispatcher recompilado.

## Inicialização e plataforma

- [ ] Loader/memória/BSS/stack/TLS/TOC/OPD integrados.
- [ ] Chamadas diretas/indiretas e módulos necessários resolvidos.
- [ ] Imports auditados por biblioteca/NID e wrappers de ABI.
- [ ] Serviços necessários sem sucesso fictício.
- [x] Árvore do disco extraída e conferida em UDF, com nomes originais e múltiplos extents.
- [ ] Tarefas SPU alcançadas executadas com sincronização correta.

## Jogo observável

- [x] Primeiro frame original conferido visualmente: logo FIFA Street, D3D12, 1280x720.
- [ ] Menu original navegável.
- [ ] Cena e conteúdo de uma partida carregados.
- [ ] Jogadores/bola/animação/física/regras funcionando.
- [ ] Controles e áudio funcionando.
- [ ] Partida completa, pausa, encerramento e retorno ao menu.
- [ ] Saves preservados e retomados após reinício.
- [ ] Progressão e modos offline da matriz verificados.

## Entrega

- [ ] Performance e estabilidade medidas com cenário e hardware registrados.
- [ ] Patches de dependências e revisões reproduzíveis no Git.
- [ ] Preparação/build/execução funcionam em checkout limpo com dados locais.
- [ ] Distribuição local funciona fora do diretório de desenvolvimento.
- [ ] Matriz final e limitações registradas.
- [ ] Todo trabalho autoral relevante commitado; dados privados fora do histórico.
- [ ] Critérios de jogo completo efetivamente atendidos.

Online, novas funções e melhorias gráficas avançadas permanecem posteriores ao
port offline funcional. Não marcar esta entrega como completa por passar testes
de funções ou por abrir uma janela.

## Continuação do FIFO e áudio

- [x] Reproduzir descarte de comandos ao abandonar park/acquire.
- [x] Instalar política FIFO do host sem resync ou reciclagem artificial.
- [x] Validar produtor real, acquires e erros de controle de fluxo.
- [ ] Integrar packet player observado em LS 0x5700 e seguir o boot estrito.
- [ ] Confirmar avanço visual além do logo e áudio não silencioso.

## PIC relocável (tasks/spu-relocatable-pic.md)

- [x] Registro/lookup PIC e ownership em duas posições: teste Windows.
- [x] Emissão de PC/links/memória relativos: fixture SPU x64 em quatro bases.
- [x] Integração optativa no manifesto/gerador com hashes e limites.
- [x] Validar entrada do sound player 1 em LS 0x7800 sem nova variante ou JIT.
- [x] Ampliar somente após conferir testes, boot e resultados observáveis.
- [x] Integrar spusend identificado em 0xac00 e continuar o boot estrito.
- [ ] Implementar cellSaveDataEnableOverlay e seguir a inicialização real.
