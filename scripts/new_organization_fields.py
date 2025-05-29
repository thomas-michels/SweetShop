from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv("../.env")

# Obter a URL do MongoDB
mongo_uri = os.getenv("DATABASE_HOST")
client = MongoClient(mongo_uri)

# Nome do banco de dados
db_name = "dev"
db = client[db_name]

# Definir os campos a serem adicionados
new_fields = {
    "$set": {
        "international_code": "+55",
        "currency": "BRL",
        "language": "pt-BR"
    }
}

# Iterar sobre a coleção organizations
total_modified = 0
collection_name = "organizations"
collection = db[collection_name]
result = collection.update_many({}, new_fields)
print(f"{result.modified_count} documentos atualizados na coleção '{collection_name}'")
total_modified += result.modified_count

print(f"Total de documentos modificados: {total_modified}")
