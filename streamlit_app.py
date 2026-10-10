import os
import streamlit as st
import sqlite3
import uuid
import main

# Load Streamlit Cloud secrets when available
try:
    for key in [
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "HUGGINGFACE_API_KEY",
        "OPENROUTER_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

main.CURRENT_SESSION_ID = st.session_state.session_id

main.load_conversation()


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

    try:
        result = main.supabase.table("messages").select(
            "provider, role, content, created_at"
        ).order(
            "id"
        ).execute()

        rows = result.data

    except Exception as e:
        st.sidebar.error(f"Could not load history: {e}")
        rows = []

    if not rows:
        st.sidebar.info("No saved history found.")

    else:
        st.sidebar.markdown("### 💬 Conversations")

        current_provider = None

        for row in rows:

            provider = row.get("provider", "Unknown")
            role = row.get("role", "Unknown")
            content = row.get("content", "")
            created_at = row.get("created_at", "")

            # New provider heading
            if provider != current_provider:

                current_provider = provider

                st.sidebar.markdown(
                    f"### 🤖 {provider.title()}"
                )

            # User message
            if role == "user":

                st.sidebar.markdown(
                    f"**You:** {content}"
                )

            # AI message
            elif role == "assistant":

                st.sidebar.markdown(
                    f"**AI:** {content}"
                )

            st.sidebar.caption(created_at)
            st.sidebar.divider()