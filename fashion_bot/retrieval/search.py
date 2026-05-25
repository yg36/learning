def retrieve_products(products, filters):

    results = products.copy()

    if "category" in filters:
        results = results[
            results["category"] == filters["category"]
        ]

    if "color" in filters:
        results = results[
            results["color"] == filters["color"]
        ]

    if "max_price" in filters:
        results = results[
            results["price"] <= filters["max_price"]
        ]

    return results