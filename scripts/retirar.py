from pymongo import MongoClient

# Conecte-se ao seu banco de dados
client = MongoClient("mongodb+srv://trodrigues:L3qVZDGLSnc5I6ps@sweetshop.04dgx.mongodb.net/")
db = client["prod"]  # Substitua pelo nome do seu banco de dados
collection = db["orders"]  # Acessa a coleção 'orders'

# Atualizar todos os documentos para remover o campo `payment_details`
result = collection.update_many({}, {"$unset": {"payment_details": ""}})

# Exibir o resultado da operação
print(f"Documentos modificados: {result.modified_count}")
