import random

def adjust_prices(base_price):
    demand_factor = random.uniform(1.0, 2.0)
    return base_price * demand_factor

if __name__ == "__main__":
    price = adjust_prices(100)
    print(f"New dynamic price: ${price:.2f}")
