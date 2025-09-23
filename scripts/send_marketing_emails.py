from __future__ import annotations

import os
import sys
from pathlib import Path
from string import Template
from typing import Any, Dict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv("../.env")

# Ensure the application package is importable when executing the script
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.dependencies.email_sender import send_email  # noqa: E402
from app.core.configs import get_environment, get_logger  # noqa: E40


EMAIL_TEMPLATE_PATH = ROOT_DIR / "templates" / "marketing_email.html"
_EMAIL_TEMPLATE: Template | None = None


def _get_email_template() -> Template:
    global _EMAIL_TEMPLATE

    if _EMAIL_TEMPLATE is None:
        try:
            template_content = EMAIL_TEMPLATE_PATH.read_text(encoding="utf-8")
        except FileNotFoundError as exc:  # pragma: no cover - defensive, depends on FS
            raise RuntimeError(
                "Marketing email template not found at 'templates/marketing_email.html'."
            ) from exc

        _EMAIL_TEMPLATE = Template(template_content)

    return _EMAIL_TEMPLATE


def _get_database() -> Collection:
    mongo_uri = os.getenv("DATABASE_HOST")

    if not mongo_uri:
        raise RuntimeError(
            "DATABASE_HOST must be defined either in the environment or the .env file."
        )

    client = MongoClient(mongo_uri)

    db_name = "dev"

    db = client[db_name]

    return db["marketing_emails"]


def _compose_message(
    email_data: Dict[str, Any]
) -> str:
    payload = {
        "name": email_data.get("name", ""),
        "email": email_data.get("email", ""),
    }
    template = _get_email_template()
    return template.substitute(payload)


def _send_marketing_emails(
    collection: Collection,
    subject: str,
) -> None:
    logger = get_logger(__name__)
    recipients: List[Dict[str, Any]] = list(collection.find())
    logger.info("Found %s marketing emails", len(recipients))

    for record in recipients:
        email = record.get("email")
        if not email:
            logger.warning("Skipping marketing email without address: %s", record)
            continue

        try:
            body = _compose_message(record)

        except KeyError as error:
            logger.error(
                "Missing placeholder '%s' for marketing email %s", error, record.get("id")
            )
            continue

        logger.info("Processing marketing email for %s", email)

        print("-- DRY RUN ----------------------------------------------------")
        print(f"To      : {email}")
        print(f"Subject : {subject}")
        print("Body    :")
        print(body)
        print("---------------------------------------------------------------")

        message_id = send_email([email], subject, body)
        if message_id:
            logger.info("Email sent to %s (message id: %s)", email, message_id)

        else:
            logger.error("Failed to send email to %s", email)


def main() -> None:
    collection = _get_database()

    _send_marketing_emails(
        collection=collection,
        subject="🚀 Grande atualização no PedidoZ + 2 meses grátis de Premium",
    )


if __name__ == "__main__":
    main()
