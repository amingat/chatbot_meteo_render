from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


def load_pdf_documents(docs_dir: str | Path):
    docs_dir = Path(docs_dir)
    documents = []
    for pdf_path in sorted(docs_dir.glob('*.pdf')):
        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()
        for page in pages:
            page.metadata['source'] = pdf_path.name
            page.metadata['page'] = int(page.metadata.get('page', 0)) + 1
        documents.extend(pages)
    return documents
