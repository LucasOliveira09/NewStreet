---
name: independent-review
description: Revisão independente e somente leitura de um incremento com evidência.
---

Solicite um auxiliar fifa_reviewer, exclusivamente modelo 6+, sem histórico completo.
Forneça raiz, escopo do diff, critérios e evidências pertinentes; não forneça uma
lista de conclusões esperadas. Nenhum segundo auxiliar concorrente.

O revisor não edita, commita, delega ou inicia build/lift/jogo. Leia o diff e os
contratos relacionados. Verifique correção, configuração efetiva, privacidade,
regressões e se a conclusão corresponde à evidência. Retorne até 250 palavras:
achados por severidade com caminho/linha e cenário; ou ausência de achados com
limitações explícitas. O principal verifica e resolve antes do commit.
