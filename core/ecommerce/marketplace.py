class Marketplace:
    def __init__(self):
        self.products = []

    def add_product(self, product):
        self.products.append(product)
        print(f"Product added: {product}")

    def list_products(self):
        for product in self.products:
            print(product)

if __name__ == "__main__":
    mkt = Marketplace()
    mkt.add_product("Smart Mirror")
    mkt.add_product("AI Beauty Assistant")
    mkt.list_products()
