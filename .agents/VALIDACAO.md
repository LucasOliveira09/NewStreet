# Validação da adaptação — 26/10/2026

Origem: kit-orquestracao-agentes-generico-modelos-2026-09-11, fornecido pelo Lucas.
Adaptação aplicada ao repositório técnico, com modelos atuais disponíveis 6+,
contexto curto, raciocínio proporcional e principal mais um auxiliar no máximo.

- `private/python-env/Scripts/python.exe tools/check_agent_setup.py`: passou.
  Quatro agentes TOML, defaults aprovados, um auxiliar e três arquivos históricos.
- Teste por mutação em cópia temporária: rejeitados modelo antigo no principal,
  modelo antigo no auxiliar, concorrência excessiva, nome de agente divergente
  e alteração de bytes no arquivo histórico. Configuração restaurada passou.
- Links locais novos conferidos; arquivos históricos preservam contexto original.
- Codex CLI 0.152.1: app-server com `--strict-config` aceitou todos os defaults
  passados como overrides somente para validação e devolveu os mesmos valores
  em `config/read`. Não iniciou tarefa de modelo, build ou jogo nesse teste.
- `config/read` sem overrides encontrou a camada de projeto, mas a informou
  desativada por ausência de confiança registrada nesta pasta. Nenhuma alteração
  de confiança, autenticação ou permissões globais foi feita.
- Agentes personalizados foram verificados por TOML e esquema documentado;
  seu carregamento em sessão confiável permanece dependente da ativação abaixo.
- Revisão independente com `gpt-6.1-sol/high`, contexto novo e somente leitura:
  corrigida a instrução final antiga do prompt que mandava reiniciar a PPU.
- Checkpoint passou de 2.085 para 78 linhas; plano, de 1.633 para 47.
  Os originais permanecem verificáveis por SHA-256. Isso não mede tokens poupados.

Para ativar: abra `D:\Ludevi\projetos\fifa-street-native` no Codex, confirme
a confiança pela interface e inicie uma sessão; confira o modelo selecionado.
O chat aberto no repositório de vídeos mantém sua própria configuração.

Evidências técnicas locais ignoradas: `private/analysis/orchestration-effective-config.json`
e `private/analysis/orchestration-schema-check.json`.
Esquema consultado: [documentação oficial](https://learn.chatgpt.com/docs/agent-configuration/subagents).
