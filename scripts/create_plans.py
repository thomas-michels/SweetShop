import requests

BASE_URL = "http://localhost:8080/api"

# Definição das features para cada plano
PLAN_FEATURES_V1 = {
    "Básico": [
        {"name": "MAX_USERS", "value": "1"},
        {"name": "MAX_PRODUCTS", "value": "20"},
        {"name": "MAX_TAGS", "value": "10"},
        {"name": "MAX_ORDERS", "value": "50"},
        {"name": "MAX_CUSTOMERS", "value": "20"},
        {"name": "MAX_EXPANSES", "value": "30"},
    ],
    "Intermediário": [
        {"name": "MAX_USERS", "value": "3"},
        {"name": "MAX_PRODUCTS", "value": "50"},
        {"name": "MAX_TAGS", "value": "30"},
        {"name": "MAX_ORDERS", "value": "200"},
        {"name": "MAX_CUSTOMERS", "value": "100"},
        {"name": "MAX_EXPANSES", "value": "100"},
        {"name": "DISPLAY_CALENDAR", "value": "true"},
        {"name": "DISPLAY_DASHBOARD", "value": "true"},
    ],
    "Avançado": [
        {"name": "MAX_USERS", "value": "10", "allowAdditional": True, "additionalPrice": 5.00},
        {"name": "MAX_PRODUCTS", "value": "150", "allowAdditional": True, "additionalPrice": 0.50},
        {"name": "MAX_TAGS", "value": "100", "allowAdditional": True, "additionalPrice": 0.20},
        {"name": "MAX_ORDERS", "value": "500", "allowAdditional": True, "additionalPrice": 0.10},
        {"name": "MAX_CUSTOMERS", "value": "300", "allowAdditional": True, "additionalPrice": 0.20},
        {"name": "MAX_EXPANSES", "value": "300", "allowAdditional": True, "additionalPrice": 0.05},
        {"name": "DISPLAY_CALENDAR", "value": "true"},
        {"name": "DISPLAY_DASHBOARD", "value": "true"},
        {"name": "DISPLAY_DELINQUENCY", "value": "true"},
    ],
}

PLAN_FEATURES_V2 = {
    "Free": [
        {"name": "MAX_USERS", "value": "1"},
        {"name": "MAX_PRODUCTS", "value": "20"},
        {"name": "MAX_TAGS", "value": "10"},
        {"name": "MAX_ORDERS", "value": "50"},
        {"name": "MAX_CUSTOMERS", "value": "20"},
        {"name": "MAX_EXPANSES", "value": "30"},
        {"name": "DISPLAY_DASHBOARD", "value": "false"},
        {"name": "DISPLAY_CALENDAR", "value": "false"},
        {"name": "DISPLAY_DELINQUENCY", "value": "false"},
        {"name": "DISPLAY_MENU", "value": "false"},
    ],
    "Básico": [
        {"name": "MAX_USERS", "value": "1"},
        {"name": "MAX_PRODUCTS", "value": "40"},
        {"name": "MAX_TAGS", "value": "20"},
        {"name": "MAX_ORDERS", "value": "100"},
        {"name": "MAX_CUSTOMERS", "value": "40"},
        {"name": "MAX_EXPANSES", "value": "60"},
        {"name": "DISPLAY_DASHBOARD", "value": "true"},
        {"name": "DISPLAY_CALENDAR", "value": "false"},
        {"name": "DISPLAY_DELINQUENCY", "value": "false"},
        {"name": "DISPLAY_MENU", "value": "false"},
    ],
    "Intermediário": [
        {"name": "MAX_USERS", "value": "3"},
        {"name": "MAX_PRODUCTS", "value": "100"},
        {"name": "MAX_TAGS", "value": "-"},
        {"name": "MAX_ORDERS", "value": "500"},
        {"name": "MAX_CUSTOMERS", "value": "100"},
        {"name": "MAX_EXPANSES", "value": "-"},
        {"name": "DISPLAY_CALENDAR", "value": "true"},
        {"name": "DISPLAY_DASHBOARD", "value": "true"},
        {"name": "DISPLAY_DELINQUENCY", "value": "true"},
        {"name": "DISPLAY_MENU", "value": "false"},
    ],
    "Premium": [
        {"name": "MAX_USERS", "value": "10"},
        {"name": "MAX_PRODUCTS", "value": "-"},
        {"name": "MAX_TAGS", "value": "-"},
        {"name": "MAX_ORDERS", "value": "-"},
        {"name": "MAX_CUSTOMERS", "value": "-"},
        {"name": "MAX_EXPANSES", "value": "-"},
        {"name": "DISPLAY_CALENDAR", "value": "true"},
        {"name": "DISPLAY_DASHBOARD", "value": "true"},
        {"name": "DISPLAY_DELINQUENCY", "value": "true"},
        {"name": "DISPLAY_MENU", "value": "true"},
    ],
}

def get_plans():
    response = requests.get(f"{BASE_URL}/plans")
    response.raise_for_status()
    return response.json()["data"]


def create_plan_feature(plan_id, feature):
    payload = {
        "planId": plan_id,
        "name": feature["name"],
        "value": feature["value"],
        "additionalPrice": feature.get("additionalPrice", 0),
        "allowAdditional": feature.get("allowAdditional", False),
    }
    response = requests.post(
        f"{BASE_URL}/plan_features",
        json=payload,
        headers={
            "Authorization": "Bearer token"
        }
    )
    response.raise_for_status()
    print(f"Feature {feature['name']} adicionada ao plano {plan_id}")

def main():
    plans = get_plans()
    for plan in plans:
        features = PLAN_FEATURES_V2.get(plan["name"])
        if not features:
            print(f"Nenhuma feature definida para o plano {plan['name']}")
            continue
        for feature in features:
            create_plan_feature(plan["id"], feature)

if __name__ == "__main__":
    main()
