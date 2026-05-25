def format_history(history):

    text = ""

    for role, message in history:

        if role == "user":
            text += f"User: {message}\n"

        else:
            text += f"Assistant: {message}\n"

    return text


def build_prompt(history_text, user_message):

    prompt = f"""
        You are a casual Indian friend chatting in Hinglish.

        Examples:

        User: goa chle?
        Assistant: Haan 😄 kab ka plan hai?

        User: kal milte h
        Assistant: Haan done

        Conversation:
        {history_text}

        User:{user_message}

        Assistant:
    """

    return prompt