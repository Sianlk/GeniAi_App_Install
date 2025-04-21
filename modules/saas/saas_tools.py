# SaaS Tools for High-Selling Products
import ecommerce_api

def identify_high_selling_products():
    print("Identifying high-selling products...")
    products = ecommerce_api.get_best_sellers()
    return products
