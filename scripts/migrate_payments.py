import requests
from pymongo import MongoClient

# Configurações do MongoDB
MONGO_URI = "mongodb://user:password@localhost:27017/"
DB_NAME = "sweet-shop"
ORDERS_COLLECTION = "orders"
bearer = "Bearer token"

# Configurações da API de pagamentos
PAYMENTS_API_URL = "http://localhost:8080/api/payments"

# Conectar ao MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
orders_collection = db[ORDERS_COLLECTION]

# Função para migrar pagamentos
def migrate_payments():
    # Buscar todos os documentos da coleção 'orders'
    orders = orders_collection.find()

    for order in orders:
        order_id = order["_id"]
        payment_details = order.get("payment_details", [])

        # Verificar se há pagamentos
        if not payment_details:
            print(f"Order {order_id} não possui detalhes de pagamento.")
            continue

        for payment in payment_details:
            # Montar o payload do pagamento
            payload = {
                "orderId": order_id,
                "method": payment["method"],
                "paymentDate": str(payment["payment_date"]),
                "amount": payment["amount"],
            }
            
            # Enviar requisição para o endpoint de pagamentos
            try:
                response = requests.post(PAYMENTS_API_URL, json=payload, headers={"x-organization": order["organization_id"], "Authorization": bearer})
                if response.status_code == 201:  # Sucesso
                    print(f"Pagamento para Order {order_id} migrado com sucesso.")
                else:
                    print(f"Falha ao migrar pagamento para Order {order_id}: {response.text}")
            except Exception as e:
                print(f"Erro ao enviar pagamento para Order {order_id}: {str(e)}")

if __name__ == "__main__":
    migrate_payments()
