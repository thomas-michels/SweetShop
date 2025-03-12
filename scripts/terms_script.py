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

# Nome da coleção
collection_name = "organizations"
collection = db[collection_name]

# Definir os campos a serem adicionados
update_fields = {
    "$set": {
        "marketing_email_consent": True,
        "terms_of_use_accepted": True
    }
}

# Atualizar todos os documentos da coleção
result = collection.update_many({}, update_fields)

print(f"{result.modified_count} documentos atualizados na coleção '{collection_name}'")
