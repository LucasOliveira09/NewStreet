# Estado para retomada

Atualizado em 24/10/2026 durante a integração de boot nativo.

## Implementação comprovada

Baseline técnico no commit `e96e614`: duas funções reais compiladas para Windows,
20.020 retornos inteiros aprovados e 16 testes do runtime aprovados.
As evidências e limites estão em `README.md` e `reports/validation.json`.
O novo executável `private/build/boot/fifa_boot.exe` executa a inicialização real
do EBOOT: TLS, mutexes, módulos, callbacks, consultas de PARAM.SFO e filesystem.
O EBOOT captura `sys_game_process_exitspawn2`, executa seu callback de encerramento
e inicia outro executável Windows com o código recompilado do FIFAZF. O teste
integrado chegou à entrada `0x23770`, com TOC `0x21d5370`, TLS de 684 bytes e
`argc=2` preservado. A cobertura incremental contém 512 funções/trechos do jogo
e 369 stubs de importação. O primeiro alvo ausente nessa cobertura é `0x17841e0`
(LR `0x23b9c`); a execução para com código 90. Não houve frame, menu ou partida.

A geração ampliada contém 98.776 entradas/trechos e está sendo compilada em
`private/build/fifazf_full`. Isso não comprova correção ou cobertura completa:
304 referências diretas permanecem com diagnóstico explícito. Foram identificados
20 ELF SPU embutidos (750.956 bytes), ainda sem execução validada neste jogo.

As quatro fronteiras de chamadas sem suporte foram exercitadas no runtime real
(HLE, syscall, chamada indireta e função não traduzida). Todas param explicitamente.
O patch do SDK está versionado e sua aplicação é idempotente. Baseline reproduzido.
Cinco testes adicionais de boot aprovam as fronteiras sem suporte, a leitura de
ponteiros de 32 bits, os argumentos exatos e o transporte para processo filho
nativo com propagação de seu código de saída, além do diagnóstico de exceção nativa.
O perfil ampliado usa `/Od` na investigação; `/O1` pode ser ativado para medição
posterior. A geração SPU não produziu um registro utilizável: seis imagens têm
palavras não decodificadas e uma tem três segmentos executáveis. O inventário
de falhas está em `private/generated/spu/inventory.json`; não foi integrado ao jogo.

## Primeira tarefa pendente

Concluir o build ampliado e executar `tools/run_native.py --profile full`.
Resolver o próximo bloqueio real de instrução, serviço ou fluxo; manter os logs
em `private/analysis/runs`. A ferramenta encerra a árvore que iniciou no timeout.
Usar os dados reais de `private/disc`; conferir `reports/native-boot-checkpoint.json`.

## Dependências conhecidas

- REA 6.7.0 recusa o ELF PPC64; usar ferramentas de análise compatíveis.
- O runtime ainda precisa ser integrado ao startup e às dependências deste jogo.
- A contagem de nomes importados não comprova serviços implementados.
- ReStreet usa a edição Xbox 360 e permanece referência para online futuro.

Mantenha código autoral, scripts e patches em commits; preserve os dados privados
fora do histórico. Atualize este estado após o próximo incremento validado.
