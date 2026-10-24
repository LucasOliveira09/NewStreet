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

- [ ] Ler instruções aplicáveis e conferir branch/HEAD/mudanças existentes.
- [x] Reproduzir baseline e registrar hardware e configuração.
- [ ] Revisar EBOOT/FIFAZF, contexto de entrada e dependências do startup.
- [ ] Dividir a integração de boot em tarefas pequenas com arquivos e aceite.
- [x] Executar inicialização real da PPU e registrar o primeiro bloqueio.
- [ ] Commitar o incremento validado e atualizar `STATUS.md`.

## Inicialização e plataforma

- [ ] Loader/memória/BSS/stack/TLS/TOC/OPD integrados.
- [ ] Chamadas diretas/indiretas e módulos necessários resolvidos.
- [ ] Imports auditados por biblioteca/NID e wrappers de ABI.
- [ ] Serviços necessários sem sucesso fictício.
- [x] Assets necessários extraídos, incluindo múltiplos extents.
- [ ] Tarefas SPU alcançadas executadas com sincronização correta.

## Jogo observável

- [ ] Primeiro frame original produzido pelo fluxo do jogo.
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
