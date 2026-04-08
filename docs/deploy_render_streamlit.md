# Déploiement Render + Streamlit Cloud

## Backend Render

- type : Web Service Python
- build command : `pip install -r requirements.txt`
- start command : `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- health check : `/health`
- persistent disk : `/opt/render/project/src/storage/memory`

### Pourquoi ce mount path

Le dossier `storage/chroma/` est déjà versionné dans le repo.
Si on montait le disk sur `storage/`, le disk masquerait `storage/chroma/` et l'index RAG ne serait plus visible.
En montant seulement `storage/memory/`, on persiste :

- `chat_history.db`
- `todo.json`

sans cacher l'index Chroma.

## Frontend Streamlit Cloud

- repo : ce repo GitHub
- file path : `streamlit_app.py`
- Python : `3.12`
- secret requis :

```toml
API_BASE_URL = "https://your-render-service.onrender.com"
```
