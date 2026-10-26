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
- [x] Integrar packet player observado em LS 0x5700 e seguir o boot estrito.
- [x] Confirmar tela de título e mix com sinal; fidelidade/sincronia pendentes.

## PIC relocável (tasks/spu-relocatable-pic.md)

- [x] Registro/lookup PIC e ownership em duas posições: teste Windows.
- [x] Emissão de PC/links/memória relativos: fixture SPU x64 em quatro bases.
- [x] Integração optativa no manifesto/gerador com hashes e limites.
- [x] Validar entrada do sound player 1 em LS 0x7800 sem nova variante ou JIT.
- [x] Ampliar somente após conferir testes, boot e resultados observáveis.
- [x] Integrar spusend identificado em 0xac00 e continuar o boot estrito.
- [x] Implementar estado e ABI void de cellSaveDataEnableOverlay.
- [ ] Continuar o boot após EnableOverlay e validar menus/saves reais.
- [x] Conferir a tela de título original e entregar Start em pacote válido.
- [x] Compilar EA Layer 3 e observar sua entrada após Start.
- [x] Integrar spugain identificado em 0x16580 e observar sua entrada real.
- [x] Identificar e compilar spuhighpassiir2 de 0x16c80.
- [x] Observar entrada real do filtro highpass.
- [x] Identificar e compilar lowpass em 0x17800.
- [x] Observar entrada real do filtro lowpass.
- [x] Identificar e compilar highshelf em 0x1d580.
- [x] Observar entrada real do filtro highshelf.
- [x] Identificar e compilar lowshelf em 0x1e300.
- [x] Observar entrada real do filtro lowshelf.
- [x] Identificar e compilar peaking em 0x1f080.
- [x] Observar entrada real do filtro peaking.
- [x] Identificar e compilar limiter1 em 0x1fe00.
- [x] Observar entrada real do limitador.
- [x] Identificar, compilar e observar pan2d1.
- [x] Admitir destinos das seis tabelas de pan2d1 após falta reproduzida.
- [x] Ultrapassar pan-cases e confirmar diálogo original após Start.
- [x] Substituir espaço livre fixo por consulta ao volume montado, com erros testados.
- [x] Conferir que free-space-verified ainda exibe o aviso, sem GetFreeSize alcançado.
- [x] Rastrear consulta fixa de 1 MiB do serviço de troféus após Start.
- [x] Instalar/verificar TRP real e confirmar desaparecimento do erro de HDD.
- [x] Confirmar aviso original de autosave e entregar Cross após revisão visual.
- [x] Implementar/validar cellSaveDataListAutoSave e gravar o primeiro perfil original.
- [x] Reproduzir e compactar fragmentação contígua de ownership SPU com guardas preservados.
- [x] Implementar cellSaveDataGetListItem e conferir metadados reais.
- [x] Confirmar releitura integral de SYS-DATA pelo código original após reinício.
- [x] Traduzir/testar job_util_job_memcpy e confirmar sua entrada após o perfil.
- [x] Traduzir AssetStream_lzma e conferir saída original contra liblzma.
- [x] Traduzir sportsutil_dxt, testar BC1/BC3 e confirmar entrada no jogo.
- [x] Traduzir dxt_encoder_job, testar 48 jobs completos e observar entrada no jogo.
- [ ] Conferir conclusão das filas concorrentes e custos de blocos não uniformes.
- [x] Traduzir aififa_topologycache_spu, executar construtores e observar sua entrada.
- [x] Traduzir Railtracks, testar quatro construtores e observar entrada no jogo.
- [x] Preservar status antes do parsing e registrar linhas inválidas sem perder eventos.
- [x] Traduzir a segunda versão ANT_kernel de 0x2030080 e observar entrada real.
- [x] Traduzir VBR e pose ANT PIC e testar construtores em quatro posições.
- [x] Permitir cabeçalho PIC parcial na pilha mantendo os bytes não executáveis.
- [x] Identificar clearactivitymasknode_exec em PC 0x5fd0.
- [x] Traduzir clearactivitymasknode_exec e confirmar sua entrada.
- [x] Observar entrada VBR e identificar o plugin seguinte em 0x2118680.
- [x] Traduzir setdofsetnode_exec de 0x2118680 e confirmar entrada.
- [x] Traduzir trajectory e scratch de 0x20e2f00/0x20be100 e confirmar entradas.
- [x] Confirmar VBR real em segunda posição LS 0x9340.
- [x] Traduzir global pose/single DOF de 0x20e6e80/0x210ca00 e confirmar entradas.
- [x] Traduzir groupnode_combine_exec de 0x20bd280 e confirmar entrada.
- [x] Traduzir DCT clip de 0x20e8c80 e confirmar entrada.
- [x] Revisar 49 módulos ANT comuns, integrar 39 novos e testar 588 chamadas originais.
- [x] Observar group final/blend no jogo após o lote.
- [x] Integrar 19 plugins SBU/ANT adicionais do mesmo CRT e validar 816 chamadas.
- [x] Observar translationscale/interactionscale no jogo.
- [x] Integrar facing angle de 0x2133c80 com cinco construtores/BSS 0xc30.
- [x] Observar headtrack/IK/contact e identificar particle IK após facing angle.
- [x] Integrar particle IK, predictable blend e mirror com testes específicos.
- [x] Observar particle IK/facial/face poser na execução real.
- [ ] Corrigir associação de rótulo distante no identificador de snapshots.
- [ ] Traduzir a imagem inicializada de 0x1ee9580 e seguir o carregamento.
- [x] Corrigir invalidação do atlas e conferir o aviso de autosave no cache normal.
- [ ] Validar preservação de save inteiro em falha de escrita e concorrência.
- [ ] Implementar metadados/grades/desbloqueios reais de troféus quando alcançados.
- [ ] Chegar ao menu navegável, à partida e à persistência completa.
