# PORTHEON como referência técnica

Inspeção somente por leitura em 26/10/2026, commit
`d3b2770246f68067d8594c0f38c52124a5901283` de
[XAndromedaXR/PORTHEON](https://github.com/XAndromedaXR/PORTHEON).
Clone local ignorado: `private/references/PORTHEON`. Nada desse projeto foi executado.

## Aplicações concretas ao FIFA

| Referência | Aplicação possível | Limite |
|---|---|---|
| [write_atomic](https://github.com/XAndromedaXR/PORTHEON/blob/d3b2770246f68067d8594c0f38c52124a5901283/src/runtime_savedata.c#L88) | Escrita temporária, flush/fsync e substituição por rename; orientar o teste pendente de save interrompido | Não importar criação automática de saves ausentes nem convenções PS4 |
| [test_probe.py](https://github.com/XAndromedaXR/PORTHEON/blob/d3b2770246f68067d8594c0f38c52124a5901283/tests/test_probe.py#L55) | Fixtures autorais para import ausente, inicializador inválido, imagem truncada e relocação fora dos limites | Relocações/instruções x86-64 não são PPU/SPU |
| [test_write_window_merge.cpp](https://github.com/XAndromedaXR/PORTHEON/blob/d3b2770246f68067d8594c0f38c52124a5901283/tests/test_write_window_merge.cpp#L2) | Reproduzir readback GPU sobrescrevendo uma escrita CPU mais recente | Vulkan/GCN não substitui RSX/D3D12; primeiro reproduzir o problema local |
| [runtime_thread.c](https://github.com/XAndromedaXR/PORTHEON/blob/d3b2770246f68067d8594c0f38c52124a5901283/src/runtime_thread.c#L1) | Estudar isolamento de ABI/TLS do guest e host | TLS FreeBSD e FS/GS são específicos do caminho PS4 x86-64 |

Prioridade: completar a tradução do bloqueio SPU atual. Aproveitar o desenho de
testes para robustez de saves e coerência gráfica quando essas tarefas forem
abordadas. Não trocar o runtime ou renderer só porque existe outra implementação.

## O que a leitura permite concluir

Há runtime, testes e investigações de execução, além do launcher. O
[README da base SacredFire](https://github.com/XAndromedaXR/PORTHEON/blob/d3b2770246f68067d8594c0f38c52124a5901283/README.SacredFire.md)
descreve execução direta do código x86-64 e serviços PS4 substituídos pelo host.
No FIFA PS3 também precisamos traduzir PPU/SPU big-endian para x64; o caminho
CPU desse projeto não elimina esse trabalho.

O README principal reúne motores diferentes; inclusive descreve Xenia Canary
para UFC Undisputed 3. A etiqueta PC port não comprova uma única arquitetura
nativa para todos os títulos listados. Esta inspeção não reproduziu gameplay.

A [investigação UFC-69](https://github.com/XAndromedaXR/PORTHEON/blob/d3b2770246f68067d8594c0f38c52124a5901283/docs/ufc3/UFC-69-host-copy-extents.md#L55)
registra log, hash e métricas de uma execução analisada pelo projeto; isso é
evidência publicada, não uma validação independente feita neste computador.

Não foi localizado contrato ANT/Replay compatível com nosso jogo. A leitura não
forneceu uma solução direta para Replay_matrixload em `0x1f1f880`.
