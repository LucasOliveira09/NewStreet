# Plano ativo do port

Estado e evidências atuais: [checkpoint](../STATUS.md).
Objetivo e aceite integral: [prompt completo](../PROMPT_EXECUCAO_COMPLETA.md).
Histórico preservado: [índice](../docs/history/README.md).

## 1. Corrigir identificação SPU fora dos limites

- Arquivos: tools/identify_spu_resident.py e testes autorais relacionados.
- Reproduzir associação errada do programa de 0x1ee9580 com nome distante.
- Vincular nomes a limites de imagem/cabeçalho revisados, rejeitando ambiguidades
  e strings truncadas; não usar busca ilimitada por BuiltElfName.
- Aceite: regressão demonstra a falha e passa; identificações válidas preservadas;
  diagnóstico da fonte atual não afirma nome original sem evidência.
- Não relaxar flags, hashes, reconhecimento de arquitetura ou saída estrita.

## 2. Traduzir a imagem fixa efetivamente carregada

- Revalidar imagem privada e duas LS contra SHA e limites no checkpoint.
- Manifesto autoral: job_raw_1ee9580, base 0x80, entrada 0xb0,
  tamanho 0x4f30, code_end 0x4a40; revisar referências e destinos indiretos.
- Cobrir entradas CRT 0x13c/0x154, BSS 0x5000..0x25a60 e dez construtores
  em ordem reversa. Não substituir chamadas originais por resultados prontos.
- Aceite: tradução sem instruções/destinos diretos pendentes, fixture de CRT
  confirma dez chamadas originais, BSS e guardas. Sem alegar algoritmo completo.
- O principal executa lift e build serializados; auxiliares não publicam gerados.

## 3. Ensaiar o avanço real após o novo módulo

- Antes de relink, conferir ausência de processos nativos pais/filhos vivos.
- Rodar os checks afetados e um probe com rótulo novo e configuração revisada.
- Preservar os cinco hashes do perfil e conferir amostras de assets pertinentes.
- Aceite: entrada real do novo módulo observada, resultado/saída registrados;
  próximo bloqueio identificado por bytes/PC, ou novo comportamento verificado.
- Saída 90 continua bloqueio válido; não a converter em sucesso.
- Atualizar checkpoint JSON/STATUS e commitar o incremento autoral validado.

## 4. Próximos marcos do produto

1. Menu original navegável e seleção de modo/time/cena.
2. Cena com jogadores, bola, animação, física e regras originais verificadas.
3. Partida completa, pausa, retorno ao menu, controles e áudio sincronizado.
4. Salvar/retomar progressão, modos offline e matriz de estabilidade/performance.
5. Build e execução reproduzíveis fora da pasta de desenvolvimento.

Só detalhar o marco seguinte quando houver evidência suficiente. Online e melhoria
visual avançada continuam posteriores à base offline funcional.
