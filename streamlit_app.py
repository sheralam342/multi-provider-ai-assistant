import os
import streamlit as st
import sqlite3
import uuid
import main

# Professional UI styling
st.markdown("""
<style>
    /* Main page */
    .stApp {
        background-color: #f5f7fb;
    }

    /* Main content width */
    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Main title */
    h1 {
        color: #172554;
        font-weight: 800;
        letter-spacing: -1px;
    }

    /* Section headings */
    h2, h3 {
        color: #1e3a8a;
    }

    /* Chat message containers */
    [data-testid="stChatMessage"] {
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        background-color: #ffffff;
    }

    /* Chat input */
    [data-testid="stChatInput"] {
        border-radius: 16px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #eef2ff;
        border-right: 1px solid #dbeafe;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: #2563eb;
        color: #1d4ed8;
    }

    /* Small captions */
    [data-testid="stCaptionContainer"] {
        color: #64748b;
    }
</style>
""", unsafe_allow_html=True)


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


st.markdown("""
<div style="padding: 10px 0 24px 0;">
    <h1 style="margin-bottom: 4px;">
        🤖 Multi-Provider AI Assistant
    </h1>
    <p style="font-size: 16px; color: #64748b;">
        One workspace. Four AI providers. Smarter conversations.
    </p>
</div>
""", unsafe_allow_html=True)


st.write(
    "Chat with Gemini, Groq, Hugging Face, or OpenRouter."
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("""
<div style="padding: 8px 0 12px 0;">
    <h2 style="margin-bottom: 4px;">⚙️ AI Control Center</h2>
    <p style="font-size: 13px; color: #64748b;">
        Select your preferred AI provider
    </p>
</div>
""", unsafe_allow_html=True)

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

# Provider information panel
provider_info = {
    "Gemini + Automatic Fallback": "Uses Gemini first, then tries other providers if needed.",
    "Gemini": "Google Gemini AI",
    "Groq": "Fast AI responses powered by Groq",
    "Hugging Face": "AI models through Hugging Face",
    "OpenRouter": "Access AI models through OpenRouter"
}

st.sidebar.info(
    f"**Selected Provider:** {provider}\n\n"
    f"{provider_info[provider]}"
)



# ============================================================
# CHAT HISTORY DISPLAY
# ============================================================

st.subheader("💬 Chat")


if "messages" not in st.session_state:

    st.session_state.messages = []


# Welcome screen for new conversations
if not st.session_state.messages:

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #dbeafe, #eef2ff);
        padding: 24px;
        border-radius: 18px;
        text-align: center;
        margin: 20px 0;
        border: 1px solid #c7d2fe;
    ">
        <h2 style="color: #1e3a8a;">👋 Welcome to your AI workspace!</h2>
        <p style="color: #475569; font-size: 16px;">
            Ask a question, learn something new, or get help with Python.
        </p>
    </div>
    """, unsafe_allow_html=True)

   
st.markdown("### 💡 Try asking")

col1, col2 = st.columns(2)

with col1:
    if st.button("🐍 Explain Python functions", use_container_width=True):
        st.session_state["suggested_question"] = "Explain Python functions with examples."

    if st.button("🔐 What is cybersecurity?", use_container_width=True):
        st.session_state["suggested_question"] = "Explain cybersecurity for a beginner."

with col2:
    if st.button("☁️ Explain cloud computing", use_container_width=True):
        st.session_state["suggested_question"] = "Explain cloud computing with examples."

    if st.button("🤖 How do AI models work?", use_container_width=True):
        st.session_state["suggested_question"] = "Explain how AI models work."




for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


# ============================================================
# USER INPUT
# ============================================================


typed_question = st.chat_input("Ask your question...")

suggested_question = st.session_state.pop(
    "suggested_question", None
)

question = typed_question or suggested_question



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
st.sidebar.subheader("💬 Chat Controls")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    st.session_state.session_id = str(uuid.uuid4())
    main.CURRENT_SESSION_ID = st.session_state.session_id
    st.session_state.messages = []
    st.session_state.pop("suggested_question", None)
    main.load_conversation()
    st.rerun()

if st.sidebar.button("🗑️ Clear Current Chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.pop("suggested_question", None)
    st.rerun()


st.sidebar.subheader("📚 Saved Chat History")

# Keep the history panel open after Streamlit reruns
if "show_saved_history" not in st.session_state:
    st.session_state.show_saved_history = False

if st.sidebar.button("View Saved History"):
    st.session_state.show_saved_history = (
        not st.session_state.show_saved_history
    )

if st.session_state.show_saved_history:

    try:
        if main.supabase is None:
            st.sidebar.warning("Supabase is not connected.")
            rows = []
        else:
            result = main.supabase.table("messages").select(
                "id, session_id, provider, role, content, created_at"
            ).order("id").execute()

            rows = result.data or []

    except Exception as e:
        st.sidebar.error(f"Could not load history: {e}")
        rows = []

    # Group messages by conversation session
    conversations = {}

    for row in rows:
        sid = row.get("session_id")

        if not sid:
            continue

        if sid not in conversations:
            conversations[sid] = []

        conversations[sid].append(row)

    # Show newest conversations first
    session_ids = list(conversations.keys())[::-1]

    if not session_ids:
        st.sidebar.info(
            "No resumable conversations found."
        )

    else:

        def conversation_label(sid):
            messages = conversations[sid]

            first_user = next(
                (
                    m for m in messages
                    if m.get("role") == "user"
                ),
                None
            )

            if first_user:
                preview = first_user.get("content", "")
                preview = preview.replace("\n", " ")[:35]
            else:
                preview = "Conversation"

            provider_name = next(
                (
                    m.get("provider")
                    for m in messages
                    if m.get("provider")
                ),
                "AI"
            )

            return f"{provider_name.title()} — {preview}"

        selected_session = st.sidebar.selectbox(
            "Choose a conversation",
            options=session_ids,
            format_func=conversation_label,
            key="history_session_selector"
        )

        if st.sidebar.button(
            "📂 Open Conversation",
            use_container_width=True
        ):

            selected_rows = conversations[selected_session]

            # Restore the selected conversation ID
            st.session_state.session_id = selected_session
            main.CURRENT_SESSION_ID = selected_session

            # Restore messages in the chat interface
            st.session_state.messages = [
                {
                    "role": row["role"],
                    "content": row.get("content", "")
                }
                for row in selected_rows
                if row.get("role") in ("user", "assistant")
            ]

            # Reload provider-specific AI conversation memory
            main.load_conversation()

            st.sidebar.success("Conversation opened!")
            st.rerun()
