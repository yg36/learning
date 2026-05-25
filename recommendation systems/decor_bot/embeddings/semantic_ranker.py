from sklearn.metrics.pairwise import cosine_similarity

from embeddings.embedder import create_embedding


def build_product_text(product):

    return f"""
    {product['name']}
    {product['category']}
    {product['style']}
    {product['material']}
    {product['color']}
    {product['room']}
    """


def semantic_rank(query, products):

    query_embedding = create_embedding(query)

    similarity_scores = []

    for _, product in products.iterrows():

        product_text = build_product_text(
            product
        )

        product_embedding = create_embedding(
            product_text
        )

        score = cosine_similarity(
            [query_embedding],
            [product_embedding]
        )[0][0]

        similarity_scores.append(score)

    products = products.copy()

    products["semantic_score"] = similarity_scores

    products = products.sort_values(
        by="semantic_score",
        ascending=False
    )

    return products