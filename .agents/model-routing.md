# Roteamento do port — modelos 6+

| Trabalho | Modelo | Raciocínio | Agente |
|---|---|---|---|
| Principal e integração | `gpt-6.1-sol` | high | sessão principal |
| Busca/triagem delimitada | `gpt-6-luna` | high | fifa_explorer |
| Implementação com aceite e arquivos exclusivos | `gpt-6.1-sol` | medium | fifa_implementer |
| Revisão independente | `gpt-6.1-sol` | high | fifa_reviewer |
| Decisão difícil após diagnóstico | `gpt-6-astra` | high | fifa_architect |

Sol 6.1, Luna 6 e Astra 6 são as versões atuais dessas famílias verificadas
em 26/10/2026 no catálogo desta sessão e na documentação oficial. Reavalie
disponibilidade antes de uma atualização; não invente nomes de modelos futuros.
Nunca escolha versão anterior a 6, mesmo se uma configuração global a sugerir.
Se um modelo não estiver disponível, use outro **6+ disponível**, registrando
a substituição; não tente contornar restrições da conta ou do cliente.

## Aplicação real

`.codex/config.toml` define o modelo principal e o teto de **um agente auxiliar**,
excluindo o principal. `.codex/agents/*.toml` define agentes descobertos pelo Codex.
Este Markdown documenta a política, mas não muda o modelo sozinho.

Abra **D:\Ludevi\projetos\fifa-street-native** como projeto e inicie uma sessão
para carregar a configuração. O chat aberto no repositório de vídeos não troca
seu modelo automaticamente. A seleção explícita da sessão e políticas gerenciadas
podem prevalecer; confira o modelo na interface antes de iniciar trabalho longo.
Não alteramos a configuração global, permissões, provedor ou autenticação.
O Codex só carrega configuração local de projetos confiáveis. Na verificação
de 26/10/2026 esta pasta ainda estava sem confiança registrada; abra o projeto
e confirme a confiança pela interface para ativar estes padrões. Até lá, os
arquivos estão instalados, mas a camada local é ignorada pelo cliente.

Quando a ferramenta não expuser os agentes personalizados, selecione explicitamente
`model` e `reasoning_effort` da tabela e passe as instruções do papel. Na ferramenta
de colaboração desta sessão, use `fork_turns: "none"` para mudar modelo/raciocínio,
com briefing autossuficiente; não combine override com histórico herdado completo.
Não finja que um agente personalizado foi carregado se houve despacho manual.

## Economia com qualidade

- Um principal por padrão; um auxiliar apenas para trabalho independente útil.
- Auxiliares não delegam. Encerre o auxiliar antes de iniciar outro.
- Use medium em implementação delimitada; high quando o risco exigir rastrear
  ABI, controle de fluxo, sincronização ou regressões. Max/ultra não são defaults.
- O principal é dono de builds, lifts, probes, patches e commits. Não abra dois
  compiladores ou ensaios para preencher a concorrência disponível.
- Briefing: objetivo; contexto mínimo; caminhos; restrições; aceite; parada;
  resultado até 250 palavras. Logs e dumps continuam em arquivos privados.
- Limites por palavras/tentativas são instruções de trabalho, não cotas nativas
  de tokens. Não há campo inventado de orçamento nesta configuração.
- Compare consumo real e marcos validados quando houver dados de uso. Mais agentes
  podem aumentar tokens; reduzir linhas de contexto não mede economia de tokens.

Fontes: [agentes e esquema](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[configuração](https://learn.chatgpt.com/docs/config-file/config-reference),
[modelos](https://developers.openai.com/api/docs/models).
