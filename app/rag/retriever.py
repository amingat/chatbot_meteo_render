\
from collections import OrderedDict

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import Settings
from app.models import SourceItem
from app.prompts import RAG_SYSTEM_PROMPT


class ClimateRAG:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise RuntimeError('OPENAI_API_KEY est requis pour utiliser le moteur RAG.')
        if not settings.chroma_path.exists():
            raise FileNotFoundError(
                "Index Chroma introuvable. Exécutez d'abord : python -m scripts.ingest --reset"
            )

        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
        self.vectorstore = Chroma(
            collection_name='climate_docs',
            persist_directory=str(settings.chroma_path),
            embedding_function=self.embeddings,
        )
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )

    def retrieve(self, query: str) -> list[tuple]:
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=self.settings.top_k,
        )
        filtered = []
        for doc, score in results:
            if score is None or score >= self.settings.rag_score_threshold:
                filtered.append((doc, score))
        return filtered

    @staticmethod
    def _format_context(results: list[tuple]) -> str:
        blocks = []
        for index, (doc, score) in enumerate(results, start=1):
            source = doc.metadata.get('source', 'source_inconnue')
            page = doc.metadata.get('page', '?')
            excerpt = doc.page_content.strip().replace('\\x00', ' ')
            score_text = f"{score:.3f}" if isinstance(score, (int, float)) else 'n/a'
            blocks.append(
                f"[Extrait {index}] source={source} | page={page} | score={score_text}\n{excerpt}"
            )
        return '\n\n'.join(blocks)

    @staticmethod
    def _deduplicate_sources(results: list[tuple]) -> list[SourceItem]:
        unique = OrderedDict()
        for doc, score in results:
            key = (doc.metadata.get('source'), doc.metadata.get('page'))
            if key not in unique:
                excerpt = doc.page_content.strip().replace('\n', ' ')
                unique[key] = SourceItem(
                    source=doc.metadata.get('source', 'source_inconnue'),
                    page=doc.metadata.get('page'),
                    excerpt=excerpt[:280] + ('...' if len(excerpt) > 280 else ''),
                    relevance=score,
                )
        return list(unique.values())

    def answer(self, query: str, history: list[dict] | None = None) -> tuple[str, list[SourceItem]]:
        results = self.retrieve(query)
        if not results:
            return (
                "Je n'ai pas trouvé d'éléments suffisamment pertinents dans les documents internes pour répondre avec certitude. Je peux compléter via la recherche web.",
                [],
            )

        context = self._format_context(results)
        history_text = ''
        if history:
            history_text = '\n'.join(f"{item['role']}: {item['content']}" for item in history[-6:])

        prompt = (
            f"Historique récent :\n{history_text or '(aucun)'}\n\n"
            f"Question utilisateur :\n{query}\n\n"
            "Contexte documentaire :\n"
            f"{context}\n\n"
            "Rédige une réponse synthétique et fiable avec citations."
        )
        response = self.llm.invoke([
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return response.content, self._deduplicate_sources(results)
