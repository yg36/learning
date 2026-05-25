def rank_products(products, user):

    products = products.copy()

    products["score"] = 0

    # rating importance
    products["score"] += products["rating"] * 20

    # gender match
    products.loc[
        products["gender"] == user["gender"],
        "score"
    ] += 30

    # younger users like trendy
    if user["age"] < 30:
        products.loc[
            products["style"] == "trendy",
            "score"
        ] += 20

    return products.sort_values(
        by="score",
        ascending=False
    )