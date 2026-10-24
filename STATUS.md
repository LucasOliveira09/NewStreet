# Estado para retomada

Atualizado em 24/10/2026 durante a integração de boot nativo.

## Implementação comprovada

Baseline técnico no commit `e96e614`: duas funções reais compiladas para Windows,
20.020 retornos inteiros aprovados e 16 testes do runtime aprovados.
As evidências e limites estão em `README.md` e `reports/validation.json`.
O novo executável `private/build/boot/fifa_boot.exe` executa a inicialização real
do EBOOT: TLS, mutexes, módulos, callbacks, consultas de PARAM.SFO e filesystem.
O caminho observado termina no import `sys_game_process_exitspawn2`, NID
`0x67f9fedb`, chamado em `0x14f68` (LR `0x14f6c`). A execução encerra com código 90
e diagnóstico estruturado. Ainda não houve entrada em FIFAZF, frame ou partida.

As quatro fronteiras de chamadas sem suporte foram exercitadas no runtime real
(HLE, syscall, chamada indireta e função não traduzida). Todas param explicitamente.
O patch do SDK está versionado e sua aplicação é idempotente. Baseline reproduzido.

## Primeira tarefa pendente

Capturar e validar os argumentos da troca de processo EBOOT -> FIFAZF; traduzir
a inicialização do executável maior e integrar seu processo nativo. Usar os dados
reais extraídos em `private/disc`; conferir `reports/native-boot-checkpoint.json`.

## Dependências conhecidas

- REA 6.7.0 recusa o ELF PPC64; usar ferramentas de análise compatíveis.
- O runtime ainda precisa ser integrado ao startup e às dependências deste jogo.
- A contagem de nomes importados não comprova serviços implementados.
- ReStreet usa a edição Xbox 360 e permanece referência para online futuro.

Mantenha código autoral, scripts e patches em commits; preserve os dados privados
fora do histórico. Atualize este estado após o próximo incremento validado.
