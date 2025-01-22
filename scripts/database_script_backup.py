from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

load_dotenv("../.env")

# Obter a URL do MongoDB
mongo_uri = os.getenv("DATABASE_HOST")

client = MongoClient(mongo_uri)

# Nome do banco de dados
db_name = "prod"
backup_dir = "./backup"

# Criar pasta para backup
os.makedirs(backup_dir, exist_ok=True)

# Conectar ao banco
db = client[db_name]

# Exportar cada coleção
for collection_name in db.list_collection_names():
    collection = db[collection_name]
    documents = list(collection.find({}))

    # Salvar cada coleção em um arquivo JSON
    with open(f"{backup_dir}/{collection_name}.json", "w", encoding="utf-8") as file:
        json.dump(documents, file, default=str, indent=4)

print(f"Backup do banco '{db_name}' concluído em {backup_dir}!")

# Restautar o backup
# mongorestore --uri="mongodb://<host>:<port>" --db=<database_name> <backup_directory>
