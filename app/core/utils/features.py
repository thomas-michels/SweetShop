from enum import Enum


class Feature(str, Enum):
    # Max values
    MAX_USERS = "MAX_USERS"
    MAX_PRODUCTS = "MAX_PRODUCTS"
    MAX_TAGS = "MAX_TAGS"
    MAX_ORDERS = "MAX_ORDERS"
    MAX_CUSTOMERS = "MAX_CUSTOMERS"
    MAX_EXPANSES = "MAX_EXPANSES"

    # Display Features
    DISPLAY_CALENDAR = "DISPLAY_CALENDAR"
    DISPLAY_DASHBOARD = "DISPLAY_DASHBOARD"
    DISPLAY_DELINQUENCY = "DISPLAY_DELINQUENCY"


def get_translation(name: Feature) -> str:
    translations = {
        Feature.MAX_USERS: "Usuários",
        Feature.MAX_PRODUCTS: "Produtos",
        Feature.MAX_TAGS: "Tags",
        Feature.MAX_ORDERS: "Pedidos por mês",
        Feature.MAX_CUSTOMERS: "Clientes",
        Feature.MAX_EXPANSES: "Despesas por mês",
        Feature.DISPLAY_CALENDAR: "Calendário",
        Feature.DISPLAY_DASHBOARD: "Painel financeiro",
        Feature.DISPLAY_DELINQUENCY: "Inadimplência",
    }
    return translations.get(name, "Recurso não encontrada")
