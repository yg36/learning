from memory import (
    create_table,
    save_message,
    get_chat_history
)

from utils import (
    format_history,
    build_prompt
)

from model import generate_response

create_table()


def chat(user_id, user_message):

    history = get_chat_history(user_id)

    history_text = format_history(history)

    prompt = build_prompt(
        history_text,
        user_message
    )

    bot_response = generate_response(
        prompt
    )

    save_message(user_id, "user", user_message)

    save_message(
        user_id,
        "assistant",
        bot_response
    )

    return bot_response