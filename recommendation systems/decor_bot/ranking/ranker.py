def rank_products(products):

    ranked = products.copy()

    ranked["score"] = (
        ranked["rating"] * 20
        +
        ranked["popularity"]
    )

    ranked = ranked.sort_values(
        by="score",
        ascending=False
    )

    return ranked