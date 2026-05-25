def retrieve_products(products, filters):

    results = products.copy()

    if "category" in filters:

        results = results[
            results["category"] == filters["category"]
        ]

    if "material" in filters:

        results = results[
            results["material"] == filters["material"]
        ]

    if "color" in filters:

        results = results[
            results["color"] == filters["color"]
        ]

    if "max_price" in filters:

        results = results[
            results["price"] <= filters["max_price"]
        ]

    if "min_price" in filters:

        results = results[
            results["price"] >= filters["min_price"]
        ]

    if "styles" in filters:

        results = results[
            results["style"].isin(filters["styles"])
        ]

    return results