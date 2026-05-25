import json

def format_response(products):

    result = []

    for _, row in products.iterrows():

        result.append({
            "id": int(row["id"]),
            "brand": row["brand"],
            "price": int(row["price"]),
            "rating": float(row["rating"]),
            "style": row["style"]
        })

    return json.dumps({
        "products": result
    }, indent=2)