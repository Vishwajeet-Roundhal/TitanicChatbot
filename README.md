# Titanic Chatbot 🤖🚢  

This is a chatbot powered by **FastAPI**, **LangChain**, and **Ollama** that answers questions based on the Titanic dataset.  

## Features ✨  
- Natural language queries on Titanic dataset  
- LLM-powered responses  
- API endpoints for easy integration  

---

# 🚀 Setup & Installation  

```bash
git repo clone https://github.com/Vishwajeet-Roundhal/TitanicChatbot.git
cd TitanicCHatbot
cd Backend
pip install -r requirements.txt
```
## Run Ollama locally
1. Install Ollama
2. Run below cmds in powershell
```
ollama pull gemma

ollama serve
```
## Run Fastapi
```
venv\Scripts\Activate
uvicorn main:app --reload
```
## Run Frontend
```
cd Frontend
pip install -r requirements.txt
venv\Scripts\Activate
streamlit run chatbot.py 
```
Make sure u run every cmd and install Ollama. Activating venv is must. 

