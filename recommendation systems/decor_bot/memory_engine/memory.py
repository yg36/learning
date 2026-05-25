memory_store = {}


def update_memory(user_id, query):

    if user_id not in memory_store:

        memory_store[user_id] = {
            "recent_queries": []
        }

    memory_store[user_id][
        "recent_queries"
    ].append(query)


def get_memory(user_id):

    return memory_store.get(user_id, {})