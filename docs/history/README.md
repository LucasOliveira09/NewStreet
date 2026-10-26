# Histórico preservado

Os três documentos anteriores foram copiados byte a byte antes da criação do
checkpoint curto em 26/10/2026. Origem, commit, tamanho e SHA-256 constam no
[manifesto](manifest.json). Contêm estados intermediários e tarefas já superadas;
o estado atual está em [STATUS.md](../../STATUS.md).

- [STATUS anterior](STATUS-2026-10-26.md)
- [Plano anterior](PLAN-2026-10-26.md)
- [Checklist anterior](TODO-2026-10-26.md)

Consulte por assunto e trecho; não carregue os arquivos inteiros em toda retomada.
A verificação em tools/check_agent_setup.py compara os bytes com o manifesto e
confere o conteúdo contra os blobs do commit de origem, considerando CRLF/LF.
O manifesto registra ambos os hashes; .gitattributes preserva os bytes do arquivo.
