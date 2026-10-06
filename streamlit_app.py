import streamlit as st
import sqlite3

# Import functions from your existing main.py
from main import (
    ask_gemini,
    ask_groq,
    ask_huggingface,
    ask_openrouter,
    ask_with_fallback
)


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="My AI Assistant",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🤖 My Multi-Provider AI Assistant")

st.write(
    "Chat with Gemini, Groq, Hugging Face, or OpenRouter."
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ AI Settings")

provider = st.sidebar.selectbox(
    "Choose an AI Provider",
    [
        "Gemini + Automatic Fallback",
        "Gemini",
        "Groq",
        "Hugging Face",
        "OpenRouter"
    ]
)


# ============================================================
# CHAT HISTORY DISPLAY
# ============================================================

st.subheader("💬 Chat")


if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


# ============================================================
# USER INPUT
# ============================================================

question = st.chat_input(
    "Ask your question..."
)


if question:

    # --------------------------------------------------------
    # Display user message
    # --------------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.write(question)


    # --------------------------------------------------------
    # Get AI response
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                # =================================================
                # GEMINI + AUTOMATIC FALLBACK
                # =================================================

                if provider == "Gemini + Automatic Fallback":

                    provider_used, answer = ask_with_fallback(
                        question
                    )

                    if provider_used is None:

                        st.error(
                            "All AI providers are currently unavailable."
                        )

                    else:

                        st.caption(
                            f"Provider used: {provider_used}"
                        )

                        st.write(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })


                # =================================================
                # GEMINI
                # =================================================

                elif provider == "Gemini":

                    answer = ask_gemini(
                        question
                    )

                    if answer is None:

                        st.error(
                            "Gemini is currently unavailable. "
                            "Try Gemini + Automatic Fallback."
                        )

                    else:

                        st.caption(
                            "Provider used: Gemini"
                        )

                        st.write(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })


                # =================================================
                # GROQ
                # =================================================

                elif provider == "Groq":

                    answer = ask_groq(
                        question
                    )

                    if answer is None:

                        st.error(
                            "Groq did not return a response."
                        )

                    else:

                        st.caption(
                            "Provider used: Groq"
                        )

                        st.write(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })


                # =================================================
                # HUGGING FACE
                # =================================================

                elif provider == "Hugging Face":

                    answer = ask_huggingface(
                        question
                    )

                    if answer is None:

                        st.error(
                            "Hugging Face did not return a response."
                        )

                    else:

                        st.caption(
                            "Provider used: Hugging Face"
                        )

                        st.write(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })


                # =================================================
                # OPENROUTER
                # =================================================

                else:

                    answer = ask_openrouter(
                        question
                    )

                    if answer is None:

                        st.error(
                            "OpenRouter did not return a response."
                        )

                    else:

                        st.caption(
                            "Provider used: OpenRouter"
                        )

                        st.write(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })


            except Exception as e:

                st.error(
                    f"Error: {e}"
                )


# ============================================================
# DATABASE HISTORY
# ============================================================

st.sidebar.divider()

st.sidebar.subheader("📚 Saved Chat History")


if st.sidebar.button("View Saved History"):

    conn = sqlite3.connect(
        "chat_history.db",
        check_same_thread=False
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT provider, role, content, created_at
        FROM messages
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()


    if not rows:

        st.sidebar.info(
            "No saved history found."
        )

    else:

        for provider_name, role, content, created_at in rows:

            if provider_name is None:

                provider_name = "Unknown"

            st.sidebar.markdown(
                f"**{provider_name.title()} — {role}**"
            )

            st.sidebar.write(
                content
            )

            st.sidebar.caption(
                created_at
            )

            st.sidebar.divider()