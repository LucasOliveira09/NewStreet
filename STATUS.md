# Estado para retomada

Atualizado em 24/10/2026 ao preparar o prompt de execução completa.

## Implementação comprovada

Baseline técnico no commit `e96e614`: duas funções reais compiladas para Windows,
20.020 retornos inteiros aprovados e 16 testes do runtime aprovados.
As evidências e limites estão em `README.md` e `reports/validation.json`.
Ainda não houve boot nativo do jogo, primeiro frame, menu ou partida.

Esta atualização acrescenta somente prompt, plano, checklist e documentação.
Não houve nova execução dos testes de código: a alteração é documental.

## Primeira tarefa pendente

Ler `PROMPT_EXECUCAO_COMPLETA.md`, conferir HEAD e mudanças existentes e reproduzir
o baseline com `tools/build.ps1`. Depois revisar EBOOT/FIFAZF e implementar uma
integração mínima que execute startup real da PPU com diagnóstico do primeiro
serviço, instrução ou alvo de chamada sem suporte.

## Dependências conhecidas

- REA 6.7.0 recusa o ELF PPC64; usar ferramentas de análise compatíveis.
- O runtime ainda precisa ser integrado ao startup e às dependências deste jogo.
- A contagem de nomes importados não comprova serviços implementados.
- ReStreet usa a edição Xbox 360 e permanece referência para online futuro.

Mantenha código autoral, scripts e patches em commits; preserve os dados privados
fora do histórico. Atualize este estado após o próximo incremento validado.
