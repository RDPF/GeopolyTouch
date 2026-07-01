# Changelog

## v0.7.2 — Cloud Hardening

Hotfix de maturidade para publicação no GitHub e Streamlit Cloud. Sem recurso matemático novo.

### Changed

- Atualização da versão do pacote para `0.7.2`.
- Troca de `use_container_width=True` por `width="stretch"` no `app.py`.
- Nomes de arquivos exportados atualizados para `v0_7_2`.
- README e roteiro de deploy atualizados.
- Resumo de catálogo atualizado para `catalog_summary_streamlit_v0_7_2.*`.

### Added

- Teste de hardening garantindo ausência de `use_container_width` no `app.py`.
- Smoke test HTTP do Streamlit na workflow do GitHub Actions.

### Unchanged

- Sem STL.
- Catálogo principal preservado.
- Diagnósticos matemáticos preservados.
- Modos de decomposição preservados.
- J6/J10 continuam como `experimental-auditado`.

## v0.7.1 — GitHub/Cloud Readiness

Release de preparação para repositório público e Streamlit Cloud.

### Added

- GitHub Actions em `.github/workflows/tests.yml` com matriz Python 3.11 / 3.12.
- `.gitignore` para Python, Streamlit, caches e exports locais.
- `LICENSE` MIT.
- `CHANGELOG.md`.
- `docs/STREAMLIT_CLOUD_DEPLOY.md` com roteiro de publicação.
- `docs/RELEASE_CHECKLIST.md` com checklist de release.
- `examples/` com arquivos OFF e JSON mínimos para testar importação.
- Testes de prontidão de repositório em `tests/test_repository_readiness.py`.
- Arquivo `.python-version` sugerindo Python 3.12.

### Changed

- Versão do pacote atualizada para `0.7.1`.
- README reescrito para uso público/GitHub.
- Pacote final limpo: preserva apenas os resumos de catálogo da versão atual.

### Unchanged

- Sem STL.
- Catálogo principal preservado.
- Diagnósticos matemáticos preservados.
- Modos de decomposição da v0.7 preservados.
- J6/J10 continuam como `experimental-auditado`.

## v0.7 — Decomposition Modes

- Modos Faces, Pirâmides face-centro, Componentes, Camadas e Vértices/arestas/faces.
- Página de decomposição.
- Manifesto e relatório HTML ampliados.

## v0.6 — Mathematical Diagnostics

- Orientação de faces, normais externas, planicidade, manifoldness e convexidade.
- Relatório técnico HTML.

## v0.5.2 — Dual Overlay Alignment

- Dual visual acompanhando explosão.
- Aviso para dual fixo com afastamento alto.

## v0.5.1 — Audit Hardening

- J6/J10 isolados como experimentais auditados.
- Validação interna do catálogo renderizado.
- Legenda adaptativa, modo silencioso e refatoração de UI.

## v0.5 — Guided Lessons

- Aula guiada por nível.
- Perguntas automáticas com gabarito.
- Exportação HTML/TXT/JSON de atividades.
