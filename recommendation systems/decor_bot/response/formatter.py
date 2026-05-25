import json


def format_response(intent, products):

    results = []

    for _, row in products.iterrows():

        results.append({

            "id": int(row["id"]),
            "brand": row["brand"],
            "name": row["name"],
            "category": row["category"],
            "style": row["style"],
            "price": int(row["price"]),
            "rating": float(row["rating"])
        })

    return json.dumps({

        "intent": intent,
        "results": results

    }, indent=2)