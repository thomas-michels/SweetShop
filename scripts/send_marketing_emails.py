"""Utility script to send the latest PedidoZ marketing campaign.

The script fetches every entry stored in the ``marketing_emails`` collection
and delivers a branded HTML message using the configured Resend integration.
The subject and key call-to-action links are provided through command-line
arguments so the campaign can be tailored as needed.

Example usage::

    python scripts/send_marketing_emails.py \
        --subject "Atualização PedidoZ + 2 meses grátis" \
        --ativar-premium-url "https://app.pedidoz.com/ativar" \
        --cta-url "https://app.pedidoz.com/login" \
        --whatsapp-link "https://wa.me/5581999999999"

If you would like to test the script without actually delivering emails, pass
the ``--dry-run`` flag.  Every email body accepts the placeholders ``name``,
``email``, ``reason`` and ``description`` and additional placeholders can be
provided through ``--extra-field``.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConfigurationError

# Ensure the application package is importable when executing the script
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.dependencies.email_sender import send_email  # noqa: E402
from app.core.configs import get_environment, get_logger  # noqa: E402


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


def _load_environment() -> None:
    """Load the environment variables from the project ``.env`` file."""

    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--subject",
        required=True,
        help="Subject that will be used for every email.",
    )
    parser.add_argument(
        "--ativar-premium-url",
        required=True,
        help="URL do botão 'Ativar meus 2 meses grátis'.",
    )
    parser.add_argument(
        "--cta-url",
        required=True,
        help="URL do botão 'Ver novidades no meu catálogo' e 'Acessar meu PedidoZ'.",
    )
    parser.add_argument(
        "--whatsapp-link",
        required=True,
        help="Link do WhatsApp usado nos botões e chamadas para contato.",
    )
    parser.add_argument(
        "--database",
        help=(
            "Mongo database name. If omitted the value from the connection "
            "string (DATABASE_HOST) will be used or defaults to 'prod'."
        ),
    )
    parser.add_argument(
        "--extra-field",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Additional placeholders available in the template in the form "
            "'key=value'. Can be provided multiple times."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only display the emails that would be sent without sending them.",
    )
    return parser


def _parse_extra_fields(pairs: Iterable[str]) -> Dict[str, str]:
    extra: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(
                f"Invalid --extra-field '{pair}'. Expected format KEY=VALUE."
            )
        key, value = pair.split("=", 1)
        extra[key.strip()] = value
    return extra


def _get_database(database_name: str | None) -> Collection:
    env = get_environment()
    mongo_uri = env.DATABASE_HOST or os.getenv("DATABASE_HOST")
    if not mongo_uri:
        raise RuntimeError(
            "DATABASE_HOST must be defined either in the environment or the .env file."
        )

    client = MongoClient(mongo_uri)

    db_name = database_name or os.getenv("MONGO_DB_NAME")
    if db_name:
        db = client[db_name]
    else:
        try:
            db = client.get_default_database()
        except ConfigurationError:
            db = client["prod"]

    return db["marketing_emails"]


def _compose_message(
    email_data: Dict[str, Any], extra_fields: Dict[str, str]
) -> str:
    payload = {
        "name": email_data.get("name", ""),
        "email": email_data.get("email", ""),
        "reason": email_data.get("reason", ""),
        "description": email_data.get("description", ""),
        "CURRENT_YEAR": str(datetime.utcnow().year),
    }
    payload.update(extra_fields)
    template = _get_email_template()
    return template.substitute(payload)


def _send_marketing_emails(
    collection: Collection,
    subject: str,
    extra_fields: Dict[str, str],
    dry_run: bool,
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
            body = _compose_message(record, extra_fields)
        except KeyError as error:
            logger.error(
                "Missing placeholder '%s' for marketing email %s", error, record.get("id")
            )
            continue

        logger.info("Processing marketing email for %s", email)

        if dry_run:
            print("-- DRY RUN ----------------------------------------------------")
            print(f"To      : {email}")
            print(f"Subject : {subject}")
            print("Body    :")
            print(body)
            print("---------------------------------------------------------------")
            continue

        message_id = send_email([email], subject, body)
        if message_id:
            logger.info("Email sent to %s (message id: %s)", email, message_id)
        else:
            logger.error("Failed to send email to %s", email)


def main() -> None:
    _load_environment()
    parser = _build_parser()
    args = parser.parse_args()

    extra_fields = _parse_extra_fields(args.extra_field)
    extra_fields["ATIVAR_PREMIUM_URL"] = args.ativar_premium_url
    extra_fields["CTA_URL"] = args.cta_url
    extra_fields["WHATSAPP_LINK"] = args.whatsapp_link
    collection = _get_database(args.database)

    _send_marketing_emails(
        collection=collection,
        subject=args.subject,
        extra_fields=extra_fields,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
