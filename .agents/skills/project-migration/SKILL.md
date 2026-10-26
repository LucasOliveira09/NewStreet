---
name: project-migration
description: Planejar e executar migração explicitamente solicitada de toolchain ou arquitetura.
---

Não ative para correções comuns. Leia o contrato existente e a revisão fixada.
Registre o problema, alternativas, impacto em ABI/patches/dados e aceite de retorno.
Faça a menor migração reversível dentro do pedido já autorizado; preserve originais,
saves e evidência. Se faltar uma decisão que mude o objetivo do usuário, apresente
a escolha concreta, enquanto avança nas partes independentes.

Valide um incremento por vez e documente rollback por commits. Não substitua
semântica por stubs para acomodar outra toolchain. O principal integra e commita.
