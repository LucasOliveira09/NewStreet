# SPU PIC recompilado com posição variável

## Objetivo e premissas

O mixer carrega os mesmos programas PIC em posições diferentes conforme seu
encadeamento. A enumeração atual de variantes estáticas interrompe o jogo a cada
posição nova. Compilar uma tradução nativa parametrizada pela posição permite
executar esses programas conhecidos sem gerar código durante o jogo.

Escopo autorizado pelo PROMPT_EXECUCAO_COMPLETA.md: implementação autônoma do
runtime e compilador, mantendo AOT, conteúdo original e falhas explícitas. Esta
mudança não adiciona um emulador de CPU nem conclui o port por si só.

Premissas conferidas: os 13 programas de áudio configurados têm cabeçalho PIC
(bit 31 do campo em +28), base alinhada a 16 e nenhum BRA/BRASL no intervalo de
código verificado. Fontes, hashes e limites continuam em spu_overlays.json.
ANT e demais programas absolutos permanecem no caminho atual.

## Contrato

- A admissão continua vinculada à origem, extensão e fingerprint do programa
  previamente traduzido. Uma posição diferente não admite código desconhecido.
- O registro PIC informa a base canônica da tradução e os limites relativos do
  código. Em um GET válido, guarda-se o deslocamento físico menos canônico em
  cada intervalo residente. Recortes de intervalos preservam esse deslocamento.
- A busca traduz somente a chave do registro: PC físico menos deslocamento.
  PC, links, registradores, dados guest e diagnósticos continuam físicos.
- Cada função PIC captura seu deslocamento em uma variável local, consultando
  o intervalo que contém o PC de entrada. Não há base global mutável. Chamadas
  diretas internas entram com PC pertencente ao mesmo programa; indiretas usam
  o dispatcher. O valor local sobrevive a callbacks e chamadas a outros módulos.
- Ajustar links BRSL/BISL/BISLED, alvos relativos, fallthrough, PC de trace,
  LQR e STQR. Preservar imediatos IL/ILA, LQA/STQA, ponteiros em registradores
  e alvos indiretos: já representam os valores arquiteturais do programa.
- O primeiro modo recusa BRA/BRASL e referências diretas fora dos limites
  auditados. Não presumir relocabilidade de código absoluto.
- Capturar o retorno físico antes de chamadas; o drain deve reconhecer entradas
  residentes relocáveis ao retomar. Não mudar as regras de retorno/terminação.
- Escritas de dados não removem código; instruções sobrescritas continuam
  invalidadas. Um intervalo desconhecido não pode cair na imagem antiga.
- Modo optativo por programa. Sem a opção, bytes gerados e comportamento das
  variantes atuais são preservados. As bases históricas podem permanecer no
  manifesto, mas o programa PIC gera uma única tradução canônica.

## Implementação e estilo

Patches fixados em patches/0001-strict-native-boot.patch. Emissão em
vendor/ps3recomp/tools/spu_lifter.py; ownership e registro em spu_channels.c e
spu_context.h; retorno em spu_drain.c. Integração em tools/lift_spu_overlays.py.
Fixtures autorais em tests/, geração privada via CMake/Boot, sem bytes do jogo
no Git. Usar nomes de API host que não vazem para a tabela de imports guest.

Exemplo conceitual de emissão, sujeito aos testes de contrato:

```c
const int32_t pic_bias = spu_code_relocation_bias(ctx);
ctx->gpr[0] = spu_link((canonical_return + pic_bias) & SPU_LS_MASK);
```

## Etapas e aceite

1. Runtime: registro PIC, deslocamento por intervalo e lookup físico/canônico.
   Fixture Windows com o mesmo programa em duas posições simultâneas, outro
   programa em posição sobreposta e integridade/invalidação. Código fixo passa.
2. Lifter: modo optativo e fixtures SPU autorais compiladas para x64. Comparar
   valores esperados em pelo menos três bases, incluindo deslocamento negativo:
   PC getter, links não-r0, chamadas diretas/indiretas, branches condicionais,
   fallthrough, LQR/STQR, LQA/STQA e retornos. Rejeitar BRA/BRASL no modo inicial.
3. Integração: manifest/generator verificam cabeçalho PIC, SHA e limites; geram
   uma tradução, preservando erro para fonte alterada/intervalo inválido. Testar
   que a flag desligada mantém a geração antiga e os testes existentes.
4. Jogo: habilitar primeiro sound player 1, cuja posição 0x7800 já foi capturada
   mas não possui variante compilada. Registrar entrada física e próximo estado
   sem interpretar CPU. Depois ampliar aos outros programas de áudio validados.

Cada etapa precisa de teste/build pertinente e commit local. Não habilitar o
modo no jogo enquanto runtime e emissão não passarem. A validação do jogo deve
separar entrada, resultado e conclusão de uma tarefa.

## Comandos de verificação

```powershell
$env:PYTHONUTF8='1'
private/python-env/Scripts/python.exe -m unittest discover -s tests
tools/build.ps1 -Target Boot
tools/build.ps1 -Target Spu
tools/build.ps1 -Target FullGame -SkipLift -WithSpu -Jobs 4
tools/build.ps1 -Target Runtime
$env:FIFA_SPU_ENTRY_TRACE='1'
private/python-env/Scripts/python.exe tools/run_native.py --timeout 65 --observe-assets
```

## Riscos e limites

Principal risco: aplicar o deslocamento duas vezes, ou a operandos absolutos.
Mitigar com dados distintos em endereços absolutos/relativos e teste de callbacks
entre dois programas PIC. Outro risco: uma busca intermediária ignorar ownership
e restaurar código antigo; testar overwrite e retomada pelo drain. Não suspender
threads nem fabricar saídas para satisfazer a fixture. Builds/cache e dados do
jogo continuam privados. Nenhuma alteração de plataforma, dependência ou fonte
de assets está incluída. Não há questão de produto pendente para esta etapa.
