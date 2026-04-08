import sys
sys.dont_write_bytecode = True


# ruff: noqa: E402

import sys
import uuid
from pathlib import Path

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings


st.set_page_config(page_title="Climate RAG Agent", page_icon="🌦️", layout="wide")

settings = get_settings()


def init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "loaded_session_id" not in st.session_state:
        st.session_state.loaded_session_id = st.session_state.session_id
    if "available_sessions" not in st.session_state:
        st.session_state.available_sessions = []
    if "api_url" not in st.session_state:
        st.session_state.api_url = settings.api_base_url


def fetch_sessions(api_url: str) -> list[dict]:
    response = requests.get(f"{api_url}/sessions", timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("sessions", [])


def load_session_messages(api_url: str, session_id: str) -> list[dict]:
    response = requests.get(f"{api_url}/sessions/{session_id}/messages", timeout=30)
    response.raise_for_status()
    payload = response.json()
    return payload.get("messages", [])


def build_session_label(session: dict) -> str:
    preview = session.get("first_message_preview") or "Session sans aperçu"
    updated_at = session.get("updated_at", "")
    count = session.get("message_count", 0)
    return f"{session['session_id']} — {preview} ({count} messages, maj: {updated_at})"


def call_health(api_url: str) -> tuple[bool, str]:
    try:
        response = requests.get(f"{api_url}/health", timeout=15)
        response.raise_for_status()
        return True, "API joignable ✅"
    except Exception as exc:
        return False, f"API non joignable: {exc}"


def send_chat(api_url: str, session_id: str, message: str) -> dict:
    response = requests.post(
        f"{api_url}/chat",
        json={"session_id": session_id, "message": message},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


init_state()

st.title("🌦️ Climate RAG Agent")
st.caption("Frontend Streamlit connecté à une API FastAPI déployée sur Render.")

with st.sidebar:
    st.subheader("Configuration")

    st.text_input("URL API Render", key="api_url")

    if st.button("Tester la connexion API", use_container_width=True):
        ok, msg = call_health(st.session_state.api_url)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    if st.button("Rafraîchir la liste des sessions", use_container_width=True):
        try:
            st.session_state.available_sessions = fetch_sessions(st.session_state.api_url)
            st.success("Liste des sessions mise à jour.")
        except Exception as exc:
            st.error(f"Impossible de récupérer les anciennes sessions: {exc}")

    st.markdown("### Session active")
    st.code(st.session_state.session_id)

    manual_session_id = st.text_input("Reprendre une session par ID", value="")

    if st.button("Charger cette session par ID", use_container_width=True):
        target_session = manual_session_id.strip()
        if not target_session:
            st.warning("Veuillez saisir un session_id existant.")
        else:
            try:
                st.session_state.messages = load_session_messages(
                    st.session_state.api_url, target_session
                )
                st.session_state.session_id = target_session
                st.session_state.loaded_session_id = target_session
                st.success(f"Session rechargée: {target_session}")
            except Exception as exc:
                st.error(f"Impossible de charger la session: {exc}")

    available_sessions = st.session_state.available_sessions
    if available_sessions:
        labels = {
            build_session_label(session): session["session_id"]
            for session in available_sessions
        }
        selected_label = st.selectbox(
            "Anciennes sessions détectées",
            options=[""] + list(labels.keys()),
            index=0,
        )

        if st.button("Reprendre la session sélectionnée", use_container_width=True):
            if not selected_label:
                st.warning("Choisissez une session dans la liste.")
            else:
                selected_session_id = labels[selected_label]
                try:
                    st.session_state.messages = load_session_messages(
                        st.session_state.api_url, selected_session_id
                    )
                    st.session_state.session_id = selected_session_id
                    st.session_state.loaded_session_id = selected_session_id
                    st.success(f"Session rechargée: {selected_session_id}")
                except Exception as exc:
                    st.error(f"Impossible de recharger la session: {exc}")

    if st.button("Créer une nouvelle session", use_container_width=True):
        st.session_state.session_id = f"streamlit-{uuid.uuid4().hex[:8]}"
        st.session_state.loaded_session_id = st.session_state.session_id
        st.session_state.messages = []
        st.success(f"Nouvelle session créée: {st.session_state.session_id}")

    if st.button("Effacer la mémoire de la session active", use_container_width=True):
        try:
            response = requests.post(
                f"{st.session_state.api_url}/memory/clear",
                json={"session_id": st.session_state.session_id},
                timeout=30,
            )
            response.raise_for_status()
            st.session_state.messages = []
            st.success("Mémoire effacée pour la session active.")
        except Exception as exc:
            st.error(f"Impossible d'effacer la mémoire: {exc}")

    st.markdown("### Exemples")
    st.markdown("- Que dit le GIEC sur 1,5°C ?")
    st.markdown("- Quelle est la météo à Paris aujourd’hui ?")
    st.markdown("- Calcule (18.5 * 4) / 3")
    st.markdown("- Ajoute à ma todo : revoir le chapitre sur les précipitations")

for message in st.session_state.messages:
    role = message.get("role", "assistant")
    content = message.get("content", "")

    with st.chat_message(role):
        st.markdown(content)

        if message.get("route"):
            st.caption(f"Route : {message['route']}")
        if message.get("used_tools"):
            st.caption("Outils: " + ", ".join(message["used_tools"]))
        if message.get("sources"):
            with st.expander("Sources"):
                for source in message["sources"]:
                    source_name = source.get("source", "Source inconnue")
                    page = source.get("page")
                    excerpt = source.get("excerpt")

                    label = f"- **{source_name}**"
                    if page:
                        label += f" — page {page}"
                    st.markdown(label)

                    if excerpt:
                        st.write(excerpt)

user_input = st.chat_input("Posez une question météo ou climat...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Réponse en cours..."):
                payload = send_chat(
                    st.session_state.api_url,
                    st.session_state.session_id,
                    user_input,
                )

            answer = payload.get("answer", "Aucune réponse renvoyée.")
            route = payload.get("route", "unknown")
            used_tools = payload.get("used_tools", [])
            sources = payload.get("sources", [])

            st.markdown(answer)
            st.caption(f"Route : {route}")

            if used_tools:
                st.caption("Outils: " + ", ".join(used_tools))

            if sources:
                with st.expander("Sources"):
                    for source in sources:
                        source_name = source.get("source", "Source inconnue")
                        page = source.get("page")
                        excerpt = source.get("excerpt")

                        label = f"- **{source_name}**"
                        if page:
                            label += f" — page {page}"
                        st.markdown(label)

                        if excerpt:
                            st.write(excerpt)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "route": route,
                    "used_tools": used_tools,
                    "sources": sources,
                }
            )

        except Exception as exc:
            error_message = f"Erreur lors de l'appel API : {exc}"
            st.error(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "route": "error",
                    "used_tools": [],
                    "sources": [],
                }
            )