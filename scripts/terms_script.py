from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv("../.env")

# Obter a URL do MongoDB
mongo_uri = os.getenv("DATABASE_HOST")
client = MongoClient(mongo_uri)

# Nome do banco de dados
db_name = "prod"
db = client[db_name]

# Definir os campos a serem removidos
remove_fields = {
    "$unset": {
        "marketing_email_consent": "",
        "terms_of_use_accepted": ""
    }
}

# Iterar sobre todas as coleções do banco de dados
total_modified = 0
for collection_name in db.list_collection_names():
    collection = db[collection_name]
    result = collection.update_many({}, remove_fields)
    print(f"{result.modified_count} documentos atualizados na coleção '{collection_name}'")
    total_modified += result.modified_count

print(f"Total de documentos modificados: {total_modified}")
