install:
	pip install --upgrade pip
	pip install -r requirements.txt

ingest:
	python scripts/ingest.py --reset

api:
	uvicorn api.main:app --reload

ui:
	streamlit run ui/streamlit_app.py
