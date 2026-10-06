from dotenv import load_dotenv
import os
import time
import sqlite3

from google import genai
from groq import Groq
from huggingface_hub import InferenceClient
import requests


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    return sqlite3.connect(
        "chat_history.db",
        check_same_thread=False
    )


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


# Add provider column if it does not exist
cursor.execute("PRAGMA table_info(messages)")
columns = [column[1] for column in cursor.fetchall()]

if "provider" not in columns:

    cursor.execute(
        "ALTER TABLE messages ADD COLUMN provider TEXT"
    )

conn.commit()

conn.close()

# ============================================================
# SAVE MESSAGE
# ============================================================

def save_message(provider, role, content):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (provider, role, content)
        VALUES (?, ?, ?)
        """,
        (provider, role, content)
    )

    conn.commit()
    conn.close()

# ============================================================
# CONVERSATION MEMORY
# ============================================================

gemini_conversation = []
groq_conversation = []
huggingface_conversation = []
openrouter_conversation = []


def load_conversation():

    # Create a new database connection for this function
    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE provider = ? OR provider IS NULL
        ORDER BY id
        """,
        ("gemini",)
    )

    for role, content in cursor.fetchall():

        if role == "user":

            gemini_conversation.append({
                "role": "user",
                "parts": [{"text": content}]
            })

        elif role == "assistant":

            gemini_conversation.append({
                "role": "model",
                "parts": [{"text": content}]
            })


    # --------------------------------------------------------
    # Groq
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE provider = ?
        ORDER BY id
        """,
        ("groq",)
    )

    for role, content in cursor.fetchall():

        groq_conversation.append({
            "role": role,
            "content": content
        })


    # --------------------------------------------------------
    # Hugging Face
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE provider = ?
        ORDER BY id
        """,
        ("huggingface",)
    )

    for role, content in cursor.fetchall():

        huggingface_conversation.append({
            "role": role,
            "content": content
        })


    # --------------------------------------------------------
    # OpenRouter
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE provider = ?
        ORDER BY id
        """,
        ("openrouter",)
    )

    for role, content in cursor.fetchall():

        openrouter_conversation.append({
            "role": role,
            "content": content
        })


    # Close this function's database connection
    conn.close()


# Load previous conversations
load_conversation()

# ============================================================
# GEMINI
# ============================================================

def ask_gemini(question):

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    messages = gemini_conversation + [
        {
            "role": "user",
            "parts": [{"text": question}]
        }
    ]

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=messages
            )

            answer = response.text

            # Save only after successful response
            gemini_conversation.append({
                "role": "user",
                "parts": [{"text": question}]
            })

            gemini_conversation.append({
                "role": "model",
                "parts": [{"text": answer}]
            })

            save_message(
                "gemini",
                "user",
                question
            )

            save_message(
                "gemini",
                "assistant",
                answer
            )

            return answer

        except Exception as e:

            error = str(e)

            # Gemini temporarily busy
            if "503" in error and attempt < 2:

                wait_time = 2 * (2 ** attempt)

                print(
                    f"Gemini is busy. "
                    f"Trying again in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            # Gemini quota exhausted
            elif "429" in error:

                print(
                    "\nGemini free quota is currently exhausted."
                )

                return None

            # Other Gemini error
            else:

                print("\nGemini error:")
                print(error)

                return None


# ============================================================
# GROQ
# ============================================================

def ask_groq(question):

    client = Groq(
        api_key=GROQ_API_KEY
    )

    messages = groq_conversation[-10:] + [
        {
            "role": "user",
            "content": question
        }
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages
    )

    answer = response.choices[0].message.content

    groq_conversation.append({
        "role": "user",
        "content": question
    })

    groq_conversation.append({
        "role": "assistant",
        "content": answer
    })

    save_message(
        "groq",
        "user",
        question
    )

    save_message(
        "groq",
        "assistant",
        answer
    )

    return answer

# ============================================================
# HUGGING FACE
# ============================================================

def ask_huggingface(question):

    client = InferenceClient(
        token=HUGGINGFACE_API_KEY
    )

    messages = huggingface_conversation[-10:] + [
        {
            "role": "user",
            "content": question
        }
    ]

    response = client.chat_completion(
        model="openai/gpt-oss-120b",
        messages=messages
    )

    answer = response.choices[0].message.content

    huggingface_conversation.append({
        "role": "user",
        "content": question
    })

    huggingface_conversation.append({
        "role": "assistant",
        "content": answer
    })

    save_message(
        "huggingface",
        "user",
        question
    )

    save_message(
        "huggingface",
        "assistant",
        answer
    )

    return answer

# ============================================================
# OPENROUTER
# ============================================================

def ask_openrouter(question):

    messages = openrouter_conversation[-10:] + [
        {
            "role": "user",
            "content": question
        }
    ]

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },

        json={
            "model": "openrouter/free",
            "messages": messages
        },

        timeout=60
    )

    data = response.json()

    if response.status_code != 200:

        print("\nOpenRouter error:")
        print(data)

        return None

    answer = data["choices"][0]["message"]["content"]

    openrouter_conversation.append({
        "role": "user",
        "content": question
    })

    openrouter_conversation.append({
        "role": "assistant",
        "content": answer
    })

    save_message(
        "openrouter",
        "user",
        question
    )

    save_message(
        "openrouter",
        "assistant",
        answer
    )

    return answer

# ============================================================
# AUTOMATIC FALLBACK
# ============================================================

def ask_with_fallback(question):

    # --------------------------------------------------------
    # 1. Gemini
    # --------------------------------------------------------

    print("\nTrying Gemini...")

    answer = ask_gemini(question)

    if answer is not None:

        return "Gemini", answer


    # --------------------------------------------------------
    # 2. Groq
    # --------------------------------------------------------

    print("\nGemini unavailable.")
    print("Trying Groq...")

    try:

        answer = ask_groq(question)

        if answer is not None:

            return "Groq", answer

    except Exception as e:

        print("\nGroq failed:")
        print(e)


    # --------------------------------------------------------
    # 3. Hugging Face
    # --------------------------------------------------------

    print("\nGroq unavailable.")
    print("Trying Hugging Face...")

    try:

        answer = ask_huggingface(question)

        if answer is not None:

            return "Hugging Face", answer

    except Exception as e:

        print("\nHugging Face failed:")
        print(e)


    # --------------------------------------------------------
    # 4. OpenRouter
    # --------------------------------------------------------

    print("\nHugging Face unavailable.")
    print("Trying OpenRouter...")

    try:

        answer = ask_openrouter(question)

        if answer is not None:

            return "OpenRouter", answer

    except Exception as e:

        print("\nOpenRouter failed:")
        print(e)


    return None, "All AI providers are currently unavailable."


# ============================================================
# CHAT HISTORY
# ============================================================

def display_history():

    conn = get_connection()
    cursor = conn.cursor()

    while True:

        cursor.execute(
            """
            SELECT provider, role, content
            FROM messages
            ORDER BY id
            """
        )

        rows = cursor.fetchall()

        if not rows:

            print("\nNo saved history found.")

            conn.close()
            return


        histories = {}


        for provider, role, content in rows:

            if not provider:
                continue

            if provider not in histories:
                histories[provider] = []

            histories[provider].append(
                (role, content)
            )


        providers = [
            "gemini",
            "groq",
            "huggingface",
            "openrouter"
        ]


        conversations = {}


        # Match questions with answers
        for provider, messages in histories.items():

            conversations[provider] = []

            question = None

            for role, content in messages:

                if role == "user":

                    question = content

                elif role == "assistant" and question is not None:

                    conversations[provider].append({
                        "question": question,
                        "answer": content
                    })

                    question = None


            if question is not None:

                conversations[provider].append({
                    "question": question,
                    "answer": "No saved answer."
                })


        # ----------------------------------------------------
        # AI HISTORY MENU
        # ----------------------------------------------------

        print("\n========== CHAT HISTORY ==========")

        for i, provider in enumerate(
            providers,
            start=1
        ):

            print(
                f"{i}. {provider.title()}"
            )

        print("0. Back to My AI Assistant")


        try:

            choice = int(
                input("\nSelect an AI: ")
            )

        except ValueError:

            print("Please enter a number.")

            continue


        if choice == 0:

            conn.close()
            return


        if choice < 1 or choice > len(providers):

            print("Invalid choice.")

            continue


        selected_provider = providers[
            choice - 1
        ]


        questions = conversations.get(
            selected_provider,
            []
        )


        if not questions:

            print(
                f"\nNo conversations found for "
                f"{selected_provider.title()}."
            )

            continue


        # ----------------------------------------------------
        # QUESTION HISTORY MENU
        # ----------------------------------------------------

        while True:

            print(
                f"\n========== "
                f"{selected_provider.upper()} HISTORY =========="
            )


            for i, item in enumerate(
                questions,
                start=1
            ):

                print(
                    f"{i}. {item['question']}"
                )


            print("0. Back to AI Selection")


            try:

                question_choice = int(
                    input("\nSelect a question: ")
                )

            except ValueError:

                print("Please enter a number.")

                continue


            if question_choice == 0:

                break


            if (
                question_choice < 1
                or question_choice > len(questions)
            ):

                print("Invalid choice.")

                continue


            selected = questions[
                question_choice - 1
            ]


            print("\n" + "=" * 50)
            print("QUESTION")
            print("=" * 50)

            print(
                selected["question"]
            )


            print("\n" + "=" * 50)
            print("ANSWER")
            print("=" * 50)

            print(
                selected["answer"]
            )

            print("=" * 50)


            back_choice = input(
                "\nPress Enter for another question, "
                "or type 0 to return to My AI Assistant: "
            )


            if back_choice == "0":

                conn.close()
                return

# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    while True:

        print("\n==============================")
        print("       MY AI ASSISTANT")
        print("==============================")


        print("\nChoose an AI:")

        print("1. Gemini")
        print("2. Groq")
        print("3. Hugging Face")
        print("4. OpenRouter")
        print("5. Exit")
        print("6. View Saved Chat History")


        choice = input(
            "\nEnter your choice: "
        )


        # ----------------------------------------------------
        # HISTORY
        # ----------------------------------------------------

        if choice == "6":

            display_history()

            continue


        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if choice == "5":

            print("\nGoodbye!")

            break


        # ----------------------------------------------------
        # INVALID CHOICE
        # ----------------------------------------------------

        if choice not in [
            "1",
            "2",
            "3",
            "4"
        ]:

            print(
                "\nInvalid choice. "
                "Please try again."
            )

            continue


        # ----------------------------------------------------
        # CHAT
        # ----------------------------------------------------

        print(
            "\nType 'exit' to return "
            "to the AI selection menu."
        )


        while True:

            question = input("\nYou: ")


            if question.lower() == "exit":

                break


            try:

                # --------------------------------------------
                # Gemini + Automatic Fallback
                # --------------------------------------------

                if choice == "1":

                    provider, answer = ask_with_fallback(
                        question
                    )


                # --------------------------------------------
                # Groq
                # --------------------------------------------

                elif choice == "2":

                    provider = "Groq"

                    answer = ask_groq(
                        question
                    )


                # --------------------------------------------
                # Hugging Face
                # --------------------------------------------

                elif choice == "3":

                    provider = "Hugging Face"

                    answer = ask_huggingface(
                        question
                    )


                # --------------------------------------------
                # OpenRouter
                # --------------------------------------------

                else:

                    provider = "OpenRouter"

                    answer = ask_openrouter(
                        question
                    )


                print("\nAI Response:")
                print("------------------------------")

                print(
                    f"Provider used: {provider}"
                )

                print("------------------------------")

                print(answer)


            except Exception as e:

                print("\nError:")
                print(e)