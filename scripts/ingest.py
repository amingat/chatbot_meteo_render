\
# ruff: noqa: E402

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings
from app.rag.indexer import build_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description='Ingestion des PDF dans Chroma.')
    parser.add_argument(
        '--reset',
        action='store_true',
        help="Supprime l'index existant avant reconstruction.",
    )
    args = parser.parse_args()

    settings = get_settings()
    chunk_count = build_vector_store(settings, reset=args.reset)
    print(f'Index construit avec succès : {chunk_count} chunks.')


if __name__ == '__main__':
    main()
