---
name: project-workflow
description: Executar um incremento verificável do port nativo com contexto mínimo.
---

1. Leia AGENTS.md, STATUS.md e a etapa corrente do plano. Preserve mudanças locais.
2. Defina comportamento, arquivos e aceite. Consulte somente a evidência pertinente.
3. Reproduza a falha relevante; implemente o menor incremento sem bypass.
4. Rode checks proporcionais. O principal serializa geração, build e ensaio real.
5. Revise semântica, privacidade e diff; use independent-review se houver risco
   substancial ou necessidade de verificação independente.
6. Commit local já autorizado. Substitua o estado atual no checkpoint; mantenha
   relatórios e histórico vinculados, sem duplicar logs ou exigir seis fases de docs.

Exploração pequena não exige auxiliar; consulte model-routing.md antes de delegar.
