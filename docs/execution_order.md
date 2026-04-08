# Ordre d’exécution

1. Créer l’environnement virtuel.
2. Installer `requirements.txt`.
3. Créer `.env` à partir de `.env.example`.
4. Vérifier que les PDF sont bien présents dans `data/pdfs/`.
5. Lancer l’ingestion :

```bash
python -m scripts.ingest --reset
```

6. Lancer l’API :

```bash
python -m uvicorn api.main:app --reload
```

7. Lancer l’interface :

```bash
python -m streamlit run ui/streamlit_app.py
```

8. Tester dans cet ordre :
   - une question RAG ;
   - une question météo ;
   - une question calculatrice ;
   - une question web ;
   - une action todo.

9. Tester la reprise de session :
   - envoyer quelques messages avec une session ;
   - recharger l’UI ;
   - choisir l’ancienne session dans la barre latérale ;
   - vérifier que l’historique réapparaît et que la conversation reprend au bon endroit.
