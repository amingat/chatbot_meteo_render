import json
from pathlib import Path

from langchain_core.tools import tool

from app.config import get_settings


def _load_todo(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding='utf-8'))


def _save_todo(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')


@tool
def todo_tool(action: str, item: str = '', index: int = -1) -> str:
    """Gère une todo locale. Actions: list, add, remove, complete."""
    settings = get_settings()
    path = settings.todo_file_path
    items = _load_todo(path)

    action = action.lower().strip()
    if action == 'list':
        if not items:
            return 'La todo est vide.'
        lines = []
        for idx, todo in enumerate(items, start=1):
            status = '✅' if todo.get('done') else '⬜'
            lines.append(f"{idx}. {status} {todo.get('text', '')}")
        return 'Todo locale:\n' + '\n'.join(lines)

    if action == 'add':
        if not item.strip():
            return 'Veuillez fournir un texte pour la tâche à ajouter.'
        items.append({'text': item.strip(), 'done': False})
        _save_todo(path, items)
        return f"Tâche ajoutée: {item.strip()}"

    if action == 'remove':
        if index < 1 or index > len(items):
            return 'Index invalide pour suppression.'
        removed = items.pop(index - 1)
        _save_todo(path, items)
        return f"Tâche supprimée: {removed.get('text', '')}"

    if action == 'complete':
        if index < 1 or index > len(items):
            return 'Index invalide pour complétion.'
        items[index - 1]['done'] = True
        _save_todo(path, items)
        return f"Tâche terminée: {items[index - 1].get('text', '')}"

    return 'Action inconnue. Utilisez list, add, remove ou complete.'
