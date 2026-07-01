# Checklist de release — v0.7.2

## Antes do commit

- [ ] Rodar `python -m pytest -q`.
- [ ] Rodar `python -m streamlit run app.py` localmente.
- [ ] Conferir `polyexplode.__version__`.
- [ ] Conferir se `README.md` menciona a versão correta.
- [ ] Conferir se existe `catalog_summary_streamlit_v0_7_2.csv`.
- [ ] Conferir se existe `catalog_summary_streamlit_v0_7_2.json`.
- [ ] Conferir que `app.py` não contém `use_container_width=True`.
- [ ] Conferir se arquivos temporários/cache não foram incluídos.

## GitHub

- [ ] Commit com mensagem clara.
- [ ] Push para `main`.
- [ ] GitHub Actions verde em Python 3.11 e 3.12.
- [ ] Smoke test Streamlit verde.
- [ ] README renderizando corretamente.
- [ ] Licença visível no repositório.

## Streamlit Cloud

- [ ] App criado com `app.py` como entry point.
- [ ] Deploy completo sem erro de dependências.
- [ ] Laboratório 3D carrega.
- [ ] Dual Explorer carrega.
- [ ] Importação OFF/JSON carrega.
- [ ] Relatórios/downloads funcionam.

## Após publicação

- [ ] Adicionar URL pública ao README.
- [ ] Opcional: substituir o badge do README pelo caminho real do repositório.
- [ ] Criar release/tag no GitHub.
