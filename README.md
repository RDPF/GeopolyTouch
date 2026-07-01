# PolyExplode Streamlit v0.7.2 — Cloud Hardening

PolyExplode é um laboratório web de anatomia geométrica de poliedros. A aplicação mostra sólidos, explode sua estrutura em modos diferentes, calcula métricas, compara dualidade, valida malhas e gera materiais didáticos.

> Versão v0.7.2: hotfix de maturidade para GitHub e Streamlit Cloud. Não adiciona recurso matemático novo; corrige depreciações de layout, reforça CI e deixa a publicação mais segura.

## Recursos principais

- Visualização 3D interativa com Streamlit + Plotly.
- Catálogo com 48 sólidos.
- Modos de decomposição:
  - faces;
  - pirâmides face-centro;
  - componentes;
  - camadas;
  - vértices/arestas/faces.
- Dual Explorer com dual progressivo e dual acompanhando a explosão.
- Diagnóstico matemático:
  - orientação de faces;
  - normais externas;
  - planaridade;
  - manifoldness;
  - convexidade provável.
- Aula guiada por nível:
  - Fundamental;
  - Médio;
  - Licenciatura;
  - Engenharia.
- Perguntas automáticas com gabarito.
- Exportação de relatórios HTML/TXT/JSON.
- Importação de arquivos OFF e JSON.
- Tema escuro por padrão.
- Sem STL.

## O que mudou na v0.7.2

- Troca de `use_container_width=True` por `width="stretch"` nas chamadas de Streamlit.
- Nomes de arquivos exportados atualizados para `v0_7_2`.
- Resumo de catálogo atualizado para `catalog_summary_streamlit_v0_7_2.*`.
- Teste automático garantindo ausência de `use_container_width` no `app.py`.
- GitHub Actions com smoke test do servidor Streamlit.
- Documentação de deploy atualizada para a versão v0.7.2.

## Rodar localmente

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

No Windows, também é possível usar:

```text
run_streamlit_windows.bat
```

## Testes

```bash
python -m pytest -q
```

A v0.7.2 inclui testes de catálogo, anatomia, dualidade, importação, aulas guiadas, hardening de auditoria, alinhamento do dual, diagnósticos matemáticos, modos de decomposição, prontidão de repositório e hardening para Streamlit Cloud.

## Deploy no Streamlit Cloud

O arquivo principal é:

```text
app.py
```

Estrutura mínima esperada no repositório:

```text
app.py
requirements.txt
.streamlit/config.toml
polyexplode/
tests/
```

Roteiro detalhado: [`docs/STREAMLIT_CLOUD_DEPLOY.md`](docs/STREAMLIT_CLOUD_DEPLOY.md).

## GitHub Actions

A workflow de testes está em:

```text
.github/workflows/tests.yml
```

Ela roda:

```bash
python -m pytest -q
```

em Python 3.11 e 3.12, além de um smoke test HTTP do Streamlit.

## Exemplos de importação

A pasta `examples/` contém:

- `examples/tetrahedron.json`;
- `examples/cube.off`.

Use esses arquivos na página **Importação** para testar o parser OFF/JSON.

## Confiabilidade geométrica

J6 e J10 continuam preservados como `experimental-auditado`. Eles são úteis para visualização didática, mas não devem ser usados como certificação métrica/formal porque a auditoria detectou malha problemática. O diagnóstico técnico mostra explicitamente esses avisos.

## Estrutura do projeto

```text
polyexplode_streamlit_v0_7_2/
├── app.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── .python-version
├── .streamlit/
│   └── config.toml
├── .github/
│   └── workflows/
│       └── tests.yml
├── docs/
│   ├── STREAMLIT_CLOUD_DEPLOY.md
│   └── RELEASE_CHECKLIST.md
├── examples/
│   ├── cube.off
│   └── tetrahedron.json
├── polyexplode/
│   ├── anatomy.py
│   ├── core.py
│   ├── custom_import.py
│   ├── decomposition.py
│   ├── diagnostics.py
│   ├── duality.py
│   ├── lessons.py
│   ├── render_plotly.py
│   ├── solids.py
│   └── ui.py
└── tests/
```

## Licença

MIT. Ver `LICENSE`.

## Status

Esta versão é indicada para publicação inicial no GitHub e teste no Streamlit Cloud.
