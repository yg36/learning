from intent.spacy_extractor import extract_intent
from retrieval.search import retrieve_products
from ranking.ranker import rank_products
from response.formatter import format_response
from memory_engine.memory import update_memory

import pandas as pd

try:
    products = pd.read_csv("data/products.csv")

    if products.empty:
        print("CSV is empty!")

    else:
        print(products.head())

except Exception as e:
    print("Error loading CSV:", e)

query = "college wear for female winter"

user = {
    "user_id": "U1",
    "age": 24,
    "gender": "male",
    "location": "Gurgaon"
}

# Step 1
filters = extract_intent(query)

# Step 2
retrieved = retrieve_products(products, filters)

# Step 3
ranked = rank_products(retrieved, user)

# Step 4
update_memory(user["user_id"], query, filters)

# Step 5
response = format_response(ranked.head(10))

print(response)