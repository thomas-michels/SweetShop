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

# Definir a operação para remover o campo 'sections'
update_operation = {
    "$unset": {
        "sections": ""
    }
}

# Iterar sobre a coleção 'products'
total_modified = 0
collection_name = "products"
collection = db[collection_name]
result = collection.update_many({}, update_operation)
print(f"{result.modified_count} documentos atualizados na coleção '{collection_name}'")
total_modified += result.modified_count

print(f"Total de documentos modificados: {total_modified}")
