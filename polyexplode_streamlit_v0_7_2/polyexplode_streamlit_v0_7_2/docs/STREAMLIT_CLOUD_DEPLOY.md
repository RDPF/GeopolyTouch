# Publicação no Streamlit Cloud — PolyExplode v0.7.2

Este roteiro assume que o repositório já foi enviado ao GitHub.

## 1. Testar localmente

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

## 2. Conferir estrutura esperada

```text
app.py
requirements.txt
.streamlit/config.toml
polyexplode/
tests/
```

O conteúdo dessa pasta deve ser a raiz do repositório. Não deixe `app.py` dentro de uma subpasta extra.

## 3. Subir para o GitHub

```bash
git init
git add .
git commit -m "Release PolyExplode Streamlit v0.7.2"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/polyexplode-lab.git
git push -u origin main
```

## 4. Criar app no Streamlit Cloud

Use estes campos:

```text
Repository: SEU_USUARIO/polyexplode-lab
Branch: main
Main file path: app.py
```

Não há dependências de sistema em `packages.txt` nesta versão.

## 5. Verificação pós-deploy

Abra o app publicado e confira:

- a página inicial carrega;
- o sólido padrão é o Dodecaedro;
- o Laboratório 3D renderiza em Plotly;
- a página Diagnóstico matemático abre;
- a Importação aceita os exemplos de `examples/`;
- downloads HTML/JSON/TXT funcionam;
- o tema escuro aparece por padrão.

## 6. CI e smoke test

A workflow `.github/workflows/tests.yml` roda:

- instalação por `requirements.txt`;
- `python -m pytest -q`;
- import smoke do pacote;
- smoke HTTP do Streamlit em `/_stcore/health`.

## 7. Observações

- O tema escuro está em `.streamlit/config.toml`.
- Não suba `.streamlit/secrets.toml`.
- O app não usa STL e não requer bibliotecas pesadas de geometria externa.
- A v0.7.2 remove chamadas depreciadas `use_container_width=True` do `app.py`.
