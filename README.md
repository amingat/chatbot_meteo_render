# Climate RAG Agent

Assistant spécialisé sur les questions **météo** et **climatiques**, avec :

- un **backend FastAPI** pour le RAG, les outils et la mémoire ;
- un **frontend Streamlit** pour l'interface utilisateur ;
- un **RAG déjà indexé** sur deux PDF du GIEC ;
- une **mémoire persistante** via SQLite ;
- une architecture prête pour **Render + Streamlit Community Cloud**.

## Architecture cible

```text
Utilisateur
   |
   v
Streamlit Cloud (frontend)
   |
   v
Render Web Service (FastAPI)
   |
   +--> RAG Chroma (storage/chroma versionné dans le repo)
   |
   +--> mémoire SQLite + todo (storage/memory persisté sur disk Render)
   |
   +--> outils météo / calculatrice / recherche web / todo
```

## Pourquoi cette version fonctionne bien sur Render et Streamlit

- **`storage/chroma/` reste dans le repo** : l'index RAG déjà construit est disponible dès le déploiement du backend.
- **Le persistent disk Render est monté uniquement sur `storage/memory/`** : on persiste les conversations et la todo sans masquer l'index Chroma fourni dans le repo.
- **Le frontend Streamlit ne dépend plus d'`OPENAI_API_KEY`** : seule l'URL du backend Render est nécessaire côté Streamlit.
- **Un `render.yaml` est fourni** pour créer le backend avec disk et variables d'environnement.

## Structure utile

```text
.
├── api/main.py
├── app/
├── data/pdfs/
├── storage/chroma/
├── storage/memory/
├── ui/streamlit_app.py
├── streamlit_app.py
├── render.yaml
├── .streamlit/secrets.toml.example
├── .env.example
└── requirements.txt
```

## Variables d'environnement backend (Render)

Le blueprint `render.yaml` configure déjà :

- `DOCS_PATH=data/pdfs`
- `CHROMA_DIR=storage/chroma`
- `SQLITE_PATH=storage/memory/chat_history.db`
- `TODO_PATH=storage/memory/todo.json`
- `OPENAI_MODEL=gpt-4o-mini`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `TOP_K=4`
- `RAG_SCORE_THRESHOLD=0.2`

À renseigner manuellement sur Render :

- `OPENAI_API_KEY`
- `TAVILY_API_KEY` (optionnel)

## Déploiement du backend sur Render

### Option recommandée : Blueprint

1. Poussez ce repo sur GitHub.
2. Dans Render, choisissez **New + > Blueprint**.
3. Sélectionnez le repo.
4. Render détectera `render.yaml`.
5. Renseignez `OPENAI_API_KEY` quand Render le demande.
6. Laissez le **disk** tel quel :
   - mount path : `/opt/render/project/src/storage/memory`
   - taille : `1 GB`
7. Déployez.

Le backend sera lancé avec :

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

Le health check est :

```text
/health
```

## Déploiement du frontend sur Streamlit Community Cloud

1. Connectez le même repo GitHub à Streamlit Community Cloud.
2. Choisissez :
   - **Branch** : `main`
   - **Main file path** : `streamlit_app.py`
3. Dans **Advanced settings**, choisissez **Python 3.12**.
4. Dans **Secrets**, collez :

```toml
API_BASE_URL = "https://your-render-service.onrender.com"
```

5. Déployez.

## Développement local

### Backend

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# ou
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
cp .env.example .env
# compléter OPENAI_API_KEY
python -m uvicorn api.main:app --reload
```

### Frontend

Dans un second terminal :

```bash
python -m streamlit run streamlit_app.py
```

## Vérifications après déploiement

### Backend Render

- `https://votre-backend.onrender.com/health`
- `https://votre-backend.onrender.com/docs`

### Frontend Streamlit

Testez :

- une question RAG : `Que dit le GIEC sur 1,5°C ?`
- une question outil : `Quelle est la météo à Paris aujourd'hui ?`
- une reprise de session dans la sidebar

## Fichiers de déploiement ajoutés

- `render.yaml`
- `streamlit_app.py`
- `.streamlit/secrets.toml.example`
- `.streamlit/config.toml`

## Remarque importante

Le fichier `.env.example` contient désormais uniquement des **placeholders**. N'y mettez jamais de vraies clés API.
