import streamlit as st
from chatbot import chat

st.set_page_config(
    page_title="Hinglish Chatbot",
    page_icon="💬",
    layout="centered"
)


st.title("💬 Hinglish Contextual Chatbot")
st.caption("Memory-based Hinglish chatbot")


# Create session memory
if "messages" not in st.session_state:
    st.session_state.messages = []


# Hardcoded user id for now
USER_ID = "yogita"

# Display old messages
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input
user_input = st.chat_input("Type your message...")


if user_input:

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Save user message in session
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )


    # Generate bot response
    bot_response = chat(
        user_id=USER_ID,
        user_message=user_input
    )


    # Show bot response
    with st.chat_message("assistant"):
        st.markdown(bot_response)
    
    # Save bot response in session
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": bot_response
        }
    )