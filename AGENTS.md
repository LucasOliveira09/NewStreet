# FIFA Street nativo — instruções de trabalho

Este repositório técnico implementa FIFA Street 2012, PS3 BLUS30882 1.00,
para Windows x64. As orientações de produção de vídeos do diretório pai
só se aplicam a pedidos de conteúdo. Responda ao Lucas em português brasileiro.

## Retomada com contexto mínimo

1. Confira `git status --short`, branch e HEAD; preserve alterações existentes.
2. Leia `STATUS.md` e a etapa atual de `tasks/plan.md`.
3. Abra somente código, testes e evidências necessários para essa etapa.
4. Consulte `PROMPT_EXECUCAO_COMPLETA.md` para os critérios completos, mudanças
   de escopo ou quando o usuário pedir sua leitura integral.
5. `reports/native-boot-checkpoint.json` registra o último ensaio do jogo.
   `docs/history/` é arquivo histórico: busque um assunto; não carregue tudo.

## Modelos e delegação

- Use exclusivamente modelos de versão 6 ou superior. Nunca faça fallback para 5.x.
- Configuração executável: `.codex/config.toml` e `.codex/agents/*.toml`.
  Roteamento e limitações: `.agents/model-routing.md`.
- Trabalhe sozinho por padrão. Para investigação independente delimitada ou
  revisão substancial, estas instruções solicitam delegação a **um auxiliar**,
  somente quando reduzir o caminho crítico ou acrescentar verificação útil.
- Teto: principal + um auxiliar, sem delegação pelos auxiliares.
- Dê contexto novo e breve, modelo e raciocínio explícitos, arquivos permitidos,
  pergunta, aceite e condição de parada. Não repasse o histórico completo.
- Principal: `gpt-6.1-sol/high`; implementação delimitada: `gpt-6.1-sol/medium`;
  exploração: `gpt-6-luna/high`; revisão: `gpt-6.1-sol/high`;
  escalada de arquitetura: `gpt-6-astra/high`, só após identificar a dificuldade.
- O principal integra e commita. Um dono por conjunto de arquivos. Builds,
  geração de SPU, execução do jogo e atualização do patch são serializados e
  pertencem ao principal. Um auxiliar de leitura não pode iniciar esses processos.
- Carregue apenas a skill necessária em `.agents/skills/`. Não transforme uma
  correção delimitada numa auditoria ou migração completa.

## Evidência e limites do port

- Código PPU/SPU compilado e runtime Windows; sem interpretador/JIT ou emulador
  como substituto da entrega. Serviços HLE precisam de semântica verificável.
- Preserve parada estrita: saída 90 é bloqueio, nunca sucesso.
- Não fabrique CELL_OK, flags, arquivos, frames ou conclusão de tarefas.
- Um teste de construtores não demonstra o algoritmo inteiro nem gameplay.
- Nome inferido é hipótese. Vincule identificação SPU a bytes, limites e hashes;
  não use o nome Replay atribuído indevidamente à fonte `0x1ee9580`.
- ISO, ELF, assets, código derivado do jogo, binários e capturas permanecem em
  áreas ignoradas. Nunca sobrescreva saves privados para facilitar um teste.
- Dependência fixada em `toolchain.lock.json`; mudanças autorais no SDK precisam
  permanecer reproduzíveis em `patches/0001-strict-native-boot.patch`.

## Execução e conclusão de incrementos

- Reproduza a falha pertinente, altere um comportamento, valide e revise o diff.
  Após duas tentativas sem informação nova, reveja a hipótese e a evidência;
  isso não cancela o trabalho autorizado nem exige uma confirmação de rotina.
- Não repita investigações ou ensaios inalterados sem uma razão registrada.
- Nunca relinke Boot/FullGame enquanto um processo nativo pai ou filho estiver
  vivo. Aguarde saída real; não considere apenas o fim do launcher.
- Não leia stderr vivo com `Get-Content -Tail`. Leia trechos limitados por bytes.
- Execute checks proporcionais. Documentação/configuração não exige rebuild do
  jogo. Mudanças no runtime exigem os testes correspondentes e patch atualizado.
- Commits locais já estão autorizados: adicione caminhos explícitos, examine o
  staged diff e rode `git diff --cached --check`. Não publique remotamente.
- Atualize o estado atual substituindo informações vencidas em `STATUS.md`
  (meta: 60–100 linhas), sem acrescentar um diário infinito. Evidências grandes
  ficam em arquivos; reporte comando, resultado, caminho e lacuna restante.
- Informe resultado, validação, commit e próximo bloqueio, sem prometer prazo,
  economia percentual de tokens ou conclusão do jogo sem evidência.
