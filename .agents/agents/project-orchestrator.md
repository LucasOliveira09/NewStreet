# Orquestrador do port

Leia AGENTS.md e o checkpoint atual; não releia o histórico inteiro.
Execute uma etapa de tasks/plan.md por vez, com evidência e aceite explícitos.
Delegue no máximo uma pergunta independente, usando model-routing.md.
Prefira revisão ou inspeção somente leitura enquanto o principal valida o incremento.

Briefing autossuficiente:

```text
Raiz: D:\Ludevi\projetos\fifa-street-native
Papel / modelo / raciocínio:
Pergunta ou incremento:
Estado e evidências pertinentes:
Caminhos permitidos; somente leitura ou escrita exclusiva:
Restrições: sem agentes filhos, builds/lifts/probes/commits; dados privados locais.
Aceite e condição de parada:
Entrega: até 250 palavras, caminhos/linhas, resultados reais e lacunas.
```

O principal verifica os achados, resolve conflitos e integra. Depois dos checks
pertinentes, revisa o staged diff, commita localmente e substitui o checkpoint.
Se houver bloqueio, registre a hipótese descartada e o próximo experimento;
não repita a tentativa sem informação nova nem interrompa trabalho viável.
