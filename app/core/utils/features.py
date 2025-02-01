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
