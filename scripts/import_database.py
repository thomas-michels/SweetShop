import json
import os
from pymongo import MongoClient

# Configurações
DATA_DIR = "./backup"  # Caminho para a pasta com os arquivos JSON
MONGO_URI = "mongodb://user:password@localhost:27017/?authSource=admin"  # URI do MongoDB
DB_NAME = "dev"  # Nome do banco de dados

# Conectar ao MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Função para importar um arquivo JSON para o MongoDB
def importar_json_para_mongodb(json_file, collection_name):
    # Abrir o arquivo JSON
    with open(json_file, 'r', encoding='utf-8') as file:
        # Carregar os dados do JSON
        dados = json.load(file)
        
        # Acessar a coleção correspondente
        collection = db[collection_name]
        
        # Inserir os dados na coleção
        if isinstance(dados, list):  # Se for uma lista de documentos
            collection.insert_many(dados)
        else:  # Se for um único documento
            collection.insert_one(dados)
    
    print(f"Dados importados com sucesso para a coleção '{collection_name}'!")

# Função para processar todos os arquivos JSON na pasta de backup
def processar_pasta_backup(backup_dir):
    # Percorrer todos os arquivos na pasta de backup
    for root, _, files in os.walk(backup_dir):
        for file in files:
            if file.endswith(".json"):
                # Caminho completo do arquivo
                file_path = os.path.join(root, file)
                
                # Nome da coleção é o nome do arquivo sem a extensão .json
                collection_name = os.path.splitext(file)[0]
                
                # Importar o arquivo JSON para o MongoDB
                print(f"Processando arquivo: {file_path}")
                importar_json_para_mongodb(file_path, collection_name)

# Executar a função para processar a pasta de backup
processar_pasta_backup(DATA_DIR)
