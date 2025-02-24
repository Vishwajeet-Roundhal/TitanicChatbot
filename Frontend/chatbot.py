import streamlit as st
import requests
import base64
from PIL import Image
import io

# Backend API URL
BACKEND_URL = "http://127.0.0.1:8000/query"

# Streamlit UI Configuration
st.set_page_config(page_title="Titanic Chatbot", page_icon="🚢", layout="wide")

# Custom CSS Styling
st.markdown("""
<style>
    .st-emotion-cache-1y4p8pa { padding: 2rem 1rem; }
    .chat-message { padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .user-message { background-color: #2b313e; border: 1px solid #3e4a5b; }
    .bot-message { background-color: #1a2835; border: 1px solid #2b3a4b; }
    .visualization-container { margin-top: 1.5rem; border: 1px solid #3e4a5b; border-radius: 0.5rem; padding: 1rem; }
    .caption { font-size: 0.8rem; color: #888; margin-top: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# Session state for chat history
if "history" not in st.session_state:
    st.session_state.history = []

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

# Page layout
st.title("🚢 Titanic Chatbot")
st.markdown("Ask questions about the Titanic incident and also get visual insights (pie chart, bar, histogram and scatterplot working as of now).")

# Chat input section
with st.container():
    col1, col2 = st.columns([6, 1])
    with col1:
        question = st.text_input(
            "Ask your question:", 
            placeholder="E.g., Show survival distribution by gender and class...",
            key="question_input"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        ask_button = st.button("Ask ➡️")



# Handle question submission
if ask_button and question.strip():
    with st.spinner("Thinking..."):
        try:
            # Send request to the backend
            response = requests.get(BACKEND_URL, params={"question": question})
            data = response.json()
            
            # Store user's question in history
            st.session_state.history.append({
                "type": "user",
                "content": question
            })
            
            # Store bot response in history
            bot_response = {
                "type": "bot",
                "text": data.get("answer", "No answer provided"),
                "visualization": data.get("visualization")
            }
            st.session_state.history.append(bot_response)
            
        except Exception as e:
            st.error(f"🚨 Error processing request: {str(e)}")

# Display chat history
for msg in st.session_state.history:
    if msg["type"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br>{msg['content']}
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.container():
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>Analyst:</strong><br>{msg['text']}
            </div>
            """, unsafe_allow_html=True)

            # Visualization Handling
            if msg.get("visualization"):
                try:
                    if msg["visualization"]:  
                        image_bytes = base64.b64decode(msg["visualization"])
                        image = Image.open(io.BytesIO(image_bytes))
                        st.markdown("""
                        <div class="visualization-container">
                            <strong>📊 Visualization</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        st.image(image, use_container_width=True)
                    else:
                        st.warning("⚠️ No visualization available.")
                except Exception as e:
                    st.error(f"🚨 Visualization Error: {e}")
