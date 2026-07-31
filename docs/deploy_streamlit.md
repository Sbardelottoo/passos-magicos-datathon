# Deploy da aplicação no Streamlit Community Cloud

O enunciado exige o deploy no **Community Cloud**. Passo a passo:

## 1. Suba o projeto para o GitHub

```bash
cd passos-magicos-datathon
git init
git add .
git commit -m "Datathon Fase 5 - Passos Magicos"
git branch -M main
git remote add origin https://github.com/<SEU_USUARIO>/passos-magicos-datathon.git
git push -u origin main
```

> Mantenha versionados `models/modelo_risco.joblib` e
> `data/processed/pede_unificado.csv` — a aplicação os carrega em tempo de
> execução. (Já estão liberados no `.gitignore`.)

## 2. Publique no Community Cloud

1. Acesse **https://share.streamlit.io** e faça login com o GitHub.
2. Clique em **"Create app"** → **"Deploy a public app from GitHub"**.
3. Preencha:
   - **Repository:** `<SEU_USUARIO>/passos-magicos-datathon`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app/app.py`
4. (Opcional) Em **Advanced settings**, selecione Python 3.11+.
5. Clique em **Deploy**. O Community Cloud instala o `requirements.txt`
   automaticamente e sobe o app.

## 3. Depois do deploy

- Copie a URL pública (formato `https://<app>.streamlit.app`) e cole no `README.md`.
- A cada `git push` na branch `main`, o app é **redeployado automaticamente**.

## Dicas / solução de problemas

- **Versão do scikit-learn:** o `requirements.txt` fixa a versão usada no treino
  para evitar avisos de incompatibilidade ao carregar o `.joblib`.
- **Arquivo não encontrado:** os caminhos em `app.py` são relativos à raiz do
  repositório (`Path(__file__).resolve().parents[1]`); mantenha a estrutura de
  pastas.
- **App "dormindo":** apps gratuitos hibernam após inatividade; o primeiro acesso
  pode levar alguns segundos para acordar.
