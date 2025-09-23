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


EMAIL_TEMPLATE = Template(
    """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Atualização PedidoZ + 2 meses grátis</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    /* Safe email defaults */
    body{margin:0;padding:0;background:#D6D8CB;font-family:Arial,Helvetica,sans-serif;color:#050505;}
    a{color:#050505;text-decoration:none;}
    .wrapper{width:100%;background:#D6D8CB;padding:24px 0;}
    .container{max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;}
    .header{background:#050505;color:#D6D8CB;padding:28px 24px;text-align:center;}
    .title{font-size:22px;margin:0 0 8px 0;font-weight:700;line-height:1.3;}
    .subtitle{font-size:14px;margin:0;opacity:0.85;}
    .content{padding:24px;}
    .h1{font-size:20px;margin:0 0 12px 0;line-height:1.35;}
    .lead{font-size:15px;line-height:1.6;margin:0 0 16px 0;}
    .badge{display:inline-block;background:#EE7B11;color:#050505;border-radius:999px;padding:8px 14px;font-weight:700;font-size:12px;letter-spacing:.3px;margin-bottom:12px;}
    .list{padding-left:18px;margin:0 0 16px 0;}
    .list li{margin-bottom:8px;line-height:1.5;}
    .cta-row{margin:22px 0; text-align:center;}
    .btn{display:inline-block;padding:14px 18px;border-radius:10px;font-weight:700;font-size:14px;margin:6px 4px;}
    .btn-primary{background:#EE7B11;color:#050505;}
    .btn-dark{background:#050505;color:#D6D8CB;}
    .btn-outline{border:2px solid #EE7B11;color:#050505;}
    .note{background:#F6F6F0;border:1px dashed #D6D8CB;border-radius:10px;padding:14px 16px;font-size:13px;margin:18px 0;line-height:1.5;}
    .footer{padding:18px 24px;text-align:center;font-size:12px;color:#050505;opacity:.8;}
    .small{font-size:12px;opacity:.9;}
    @media (prefers-color-scheme: dark) {
      body{background:#050505;color:#D6D8CB;}
      .container{background:#111111;}
      .footer{color:#D6D8CB;}
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <div class="title">🚀 Grande atualização no PedidoZ</div>
        <div class="subtitle">Pedidos mais rápidos, catálogo mais bonito e novas formas de vender</div>
      </div>

      <div class="content">
        <span class="badge">🎁 2 MESES DE PREMIUM GRÁTIS</span>
        <p class="lead">
          Para comemorar esta atualização, estamos oferecendo <strong>2 meses grátis do plano Premium</strong> para todos os clientes e novas contas criadas até <strong>15/10</strong>.
        </p>

        <h1 class="h1">O que há de novo</h1>
        <ul class="list">
          <li><strong>Pedidos, produtos e catálogo atualizados</strong> para mais agilidade.</li>
          <li><strong>Adicionais nos produtos</strong> para personalizar cada pedido.</li>
          <li><strong>Ofertas agrupadas com desconto</strong> — fixas ou por tempo limitado.</li>
          <li><strong>Melhorias visuais no catálogo</strong> para sua vitrine online.</li>
          <li><strong>Conta do cliente</strong> + <strong>histórico de pedidos</strong> para mais autonomia.</li>
          <li><strong>Pré-pedidos aprimorados</strong> com <em>navegação mais simples e rápida</em>.</li>
        </ul>

        <div class="cta-row">
          <a href="${ATIVAR_PREMIUM_URL}" class="btn btn-primary">Ativar meus 2 meses grátis</a>
          <a href="${CTA_URL}" class="btn btn-dark">Ver novidades no meu catálogo</a>
          <a href="${WHATSAPP_LINK}" class="btn btn-outline">Falar no WhatsApp</a>
        </div>

        <div class="note">
          Precisa de ajuda para configurar adicionais, criar ofertas ou utilizar as novas funções?
          Nosso time oferece <strong>treinamentos rápidos</strong> e suporte no <strong>WhatsApp</strong>.
        </div>

        <p class="small">
          Dúvidas? <a href="${WHATSAPP_LINK}"><strong>Chame no WhatsApp</strong></a> ou responda este e-mail.
        </p>

        <div class="cta-row">
          <a href="${WHATSAPP_LINK}" class="btn btn-primary">📲 Abrir WhatsApp</a>
          <a href="${CTA_URL}" class="btn btn-dark">🚀 Acessar meu PedidoZ</a>
        </div>
      </div>

      <div class="footer">
        © ${CURRENT_YEAR} PedidoZ — Todas as novidades, sem custo, por tempo limitado.<br>
        Oferta válida para contas novas e existentes criadas/ativas até <strong>15/10</strong>.
      </div>
    </div>
  </div>
</body>
</html>
"""
)


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
    return EMAIL_TEMPLATE.substitute(payload)


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
