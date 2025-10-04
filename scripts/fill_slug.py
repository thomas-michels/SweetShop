from pymongo import MongoClient
import os
from dotenv import load_dotenv

from app.core.utils.slugify import slugify

# Carregar variáveis de ambiente
load_dotenv(".env")

# Obter a URL do MongoDB
mongo_uri = os.getenv("DATABASE_HOST")
client = MongoClient(mongo_uri)

# Nome do banco de dados
db_name = "dev"
db = client[db_name]

menus = list(db["menus"].find())

print(f"{len(menus)} menus found")

for menu in menus:
    if menu.get("slug") is None or menu["slug"] == "":
        print(f"slugging -> {menu["name"]}")

        db["menus"].update_one(
            {"_id": menu["_id"]},
            {"$set": {"slug": slugify(menu["name"])}}
        )

organizations = list(db["organizations"].find())

print(f"{len(organizations)} organizations found")

for org in organizations:
    if org.get("slug") is None or org["slug"] == "":
        print(f"slugging -> {org["name"]}")

        db["organizations"].update_one(
            {"_id": org["_id"]},
            {"$set": {"slug": slugify(org["name"])}}
        )
