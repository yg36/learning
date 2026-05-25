memory_store = {}

def update_memory(user_id, query, filters):

    if user_id not in memory_store:
        memory_store[user_id] = {
            "recent_searches": []
        }

    memory_store[user_id]["recent_searches"].append(query)

    if "category" in filters:
        memory_store[user_id]["favorite_category"] = filters["category"]