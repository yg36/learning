import pandas as pd

from intent.spacy_extractor import extract_intent

from retrieval.search import retrieve_products

from embeddings.semantic_ranker import semantic_rank

from response.formatter import format_response


products = pd.read_csv(
    "data/products.csv"
)


query = "minimal wooden coffee table under 10k"


# -------------------------
# INTENT EXTRACTION
# -------------------------

intent = extract_intent(query)

print("\nINTENT:")
print(intent)


# -------------------------
# RETRIEVAL
# -------------------------

retrieved_products = retrieve_products(
    products,
    intent
)

print("\nRETRIEVED:")
print(
    retrieved_products[
        ["name", "price"]
    ]
)


# -------------------------
# SEMANTIC RANKING
# -------------------------

ranked_products = semantic_rank(
    query,
    retrieved_products
)

print("\nSEMANTIC RESULTS:")
print(
    ranked_products[
        ["name", "semantic_score"]
    ]
)


# -------------------------
# FINAL RESPONSE
# -------------------------

response = format_response(
    intent,
    ranked_products.head(5)
)

print("\nFINAL RESPONSE:")
print(response)