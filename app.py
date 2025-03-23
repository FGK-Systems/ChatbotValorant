import streamlit as st
import requests
import google.generativeai as genai
import time
import firebase_admin
from firebase_admin import credentials, firestore, auth
from uuid import uuid4
import os
from dotenv import load_dotenv
from firebase_admin import auth
import requests
import json

# ------------------------------ CONFIGURAÇÃO INICIAL STREAMLIT -------------------------------
st.set_page_config(
    page_title="Riot Valorant",
    layout="centered",
    page_icon="https://img.icons8.com/?size=100&id=GjCK2f2wpZxt&format=png&color=000000"
)
# -----------------------------------------------------------------------------------------------

# ------------------------------ CONFIGURAÇÃO DO GEMINI ----------------------------------------
load_dotenv()
key_gemini = os.getenv("API_KEY_GEMINI")
key_firebase = os.getenv("API_KEY_FIREBASE")
genai.configure(api_key=key_gemini)

@st.cache_resource
def load_gemini():
    return genai.GenerativeModel('gemini-1.5-pro')

model = load_gemini() 
# --------------------------------------------------------------------------------------------------

# ------------------------------ CONFIGURAÇÃO FIREBASE --------------------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")  
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ------------------------------ FUNÇÕES DE AUTENTICAÇÃO FIREBASE ------------------------------
BASE_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key_firebase}"
# Função para autenticar o usuário (Login)
def login(email, senha):
    try:
        payload = {
            "email": email,
            "password": senha,
            "returnSecureToken": True
        }
        response = requests.post(BASE_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            return {"user_id": data["localId"], "id_token": data["idToken"]}
        else:
            print("Erro ao autenticar:", response.json().get("error", {}).get("message", "Desconhecido"))
            return None
    except Exception as e:
        print(f"Erro ao autenticar: {str(e)}")
        return None

# Função para criar um novo usuário
def create_account(email, senha):
    try:
        # Criação de usuário com e-mail e senha
        user = auth.create_user(
            email=email,
            password=senha
        )
        return user.uid
    except auth.AuthError as e:
        print(f"Erro ao criar conta: {str(e)}")
        return None

# ------------------------------ LÓGICA PARA SELEÇÃO DO USUÁRIO ----------------------------

# Função que retorna o ID do usuário atual
def get_user_id():
    if "user_id" in st.session_state:
        return st.session_state.user_id
    return None

def load_chat_history():
    user_id = get_user_id()
    if user_id is None:
        return []  # Nenhum usuário logado
    doc_ref = db.collection("chats").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("history", [])
    return []

def save_chat_message(role, message, image_url=None):
    user_id = get_user_id()
    if user_id is None:
        return  # Nenhum usuário logado, não salva
    doc_ref = db.collection("chats").document(user_id)
    
    new_message = {
        "role": role,
        "message": message,
        "image_url": image_url,
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    doc_ref.set({
        "history": firestore.ArrayUnion([new_message]),
        "last_modified": firestore.SERVER_TIMESTAMP
    }, merge=True)

# ------------------------------ FUNCIONALIDADES DO CHATBOT -----------------------------------
def display_chat():
    for entry in st.session_state.conversation_history:
        role = entry["role"]
        message = entry["message"]
        image_url = entry.get("image_url", None)
        timestamp = entry.get("timestamp", "")
        
        if role == "user":
            st.markdown(
                f"""
                <div style='text-align: right; margin: 10px;'>
                    <div style='color: #666; font-size: 0.8em;'>{timestamp}</div>
                    <div style='background: #ff0000; color: white; padding: 10px; border-radius: 15px; display: inline-block;'>
                        {message}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style='text-align: left; margin: 10px;'>
                    <div style='color: #666; font-size: 0.8em;'>{timestamp}</div>
                    <div style='color: #000; background: #f1f0f0; padding: 10px; border-radius: 15px; display: inline-block;'>
                        {message}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if image_url:
                st.image(image_url, width=150)

def uuid_agente(agente):
    agent_dict = {
        "gekko": "e370fa57-4757-3604-3648-499e1f642d3f",
        "fade": "dade69b4-4f5a-8528-247b-219e5a1facd6",
        "neon": "bb2a4828-46eb-8cd1-e765-15848195d751",
        "chamber": "22697a3d-45bf-8dd7-4fec-84a9e28c69d7",
        "kay/o": "601dbbe7-43ce-be57-2a40-4abd24953621",
        "astra": "41fb69c1-4189-7b37-f117-bcaf1e96f1bf",
        "yoru": "7f378557-64e0-494d-862d-ec5590b48748",
        "skye": "6f2a04ca-43e0-be17-7f36-b3908627744d",
        "reyna": "a3bfb853-43b2-7238-a4f1-ad90e9e46bcc",
        "raze": "f94c3b30-42be-e959-889c-5aa313dba261",
        "breach": "5f8d3a7f-467b-97f3-062c-13acf203c006",
        "omen": "8e253930-4c05-31dd-1b6c-968525494517",
        "cypher": "117ed9e3-49f3-6512-3ccf-0cada7e3823b",
        "sova": "320b2a48-4d9b-a075-30f1-1f93a9b638fa",
        "sage": "569fdd95-4d10-43ab-ca70-79becc718b46",
        "phoenix": "eb93336a-449b-9c1b-0a54-a891f7921d69",
        "jett": "add6443a-41bd-e414-f6ad-e58d267f4e95",
        "viper": "707eab51-4836-f488-046a-cda6bf494859",
        "brimstone": "9f0d8ba9-4140-b941-57d3-a7ad57c6b417",
        "harbor": "95b78ed7-4637-86d9-7e41-71ba8c293152"
    }
    return agent_dict.get(agente,'')

def consulta_api_valorant(agente):
    uuid = uuid_agente(agente)
    response = requests.get(f"https://valorant-api.com/v1/agents/{uuid}")
    if response.status_code == 200:
        print('--')
        data = response.json()
    
        agente_info = {
            "name": data["data"]["displayName"].capitalize() if "data" in data else "N/A",  # Acessa a chave 'data' se existir
            "id": data["data"]["uuid"] if "data" in data else "N/A",
            "description": data["data"]["description"] if "data" in data else "N/A",
            "image_url": data["data"]["fullPortrait"] if "data" in data else "N/A",
            "abilities": [
                {
                    "name": abilitie["displayName"] if "displayName" in abilitie else "N/A",
                    "description": abilitie["description"] if "description" in abilitie else "N/A",
                    "icon": abilitie["displayIcon"] if "displayIcon" in abilitie else "N/A"
                } for abilitie in data["data"].get("abilities", [])
            ] if "data" in data else []
        }
        return agente_info
    else:
        return None
    
def consultando_nome_agente(agente_input):
    agentes_conhecidos = [
        "gekko", "fade", "neon", "chamber", "kay/o", "astra", "yoru", 
        "skye", "reyna", "raze", "breach", "omen", "cypher", "sova", 
        "sage", "phoenix", "jett", "viper", "brimstone", "harbor"
    ]

    for agente in agentes_conhecidos:
        if agente in agente_input:
            return agente
    return None

def generate_response(user_input):
    try:
        start_time = time.time()
        
        # Extraindo nome do Agente da pergunta
        frase = user_input.lower().split()
        dados_encontrados = None

        for palavra in frase:
            agente = consultando_nome_agente(palavra)
            if agente:
                dados_encontrados = consulta_api_valorant(agente)
                if dados_encontrados and "erro" not in dados_encontrados:
                    break
        
        # Se a pergunta for sobre um agente específico
        if dados_encontrados:
            # Criando o contexto para o Gemini
            context = f"""
            Nome: {dados_encontrados['name']}
            ID: {dados_encontrados['id']}
            Descricao: {dados_encontrados['description']}
            """
            # Adicionando as habilidades ao contexto de forma formatada
            for abilitie in dados_encontrados['abilities']:
                context += f"""
                - {abilitie['name']}: {abilitie['description']}
                """
            
            prompt = f"""
            Você é um assistente especializado em Valorant.
            Forneça informações detalhadas usando o contexto abaixo:

            {context}

            Pergunta do usuário: {user_input}

            Resposta:
            """
        else:
            # Se a pergunta for genérica sobre Valorant
            prompt = f"""
            Você é um assistente especializado em Valorant.
            Responda à pergunta do usuário de forma clara e detalhada:

            Pergunta do usuário: {user_input}

            Resposta:
            """
        
        # Gera a resposta usando o Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=200
            )
        )
        
        return {
            "text": response.text if response.text else "Informação não encontrada.",
            "image_url": dados_encontrados['image_url'] if dados_encontrados else None
        }
        
    except Exception as e:
        return {"text": f"Erro no sistema: {str(e)}", "image_url": None}


# ------------------------------ INTERFACE DE LOGIN E CADASTRO ----------------------------

def login_or_register():
    st.title("Login ou Cadastro")
    
    # Opções de Login ou Cadastro
    login_or_register = st.radio("Escolha uma opção", ["Login", "Cadastro"])
    
    email = st.text_input("Digite seu e-mail")
    senha = st.text_input("Digite sua senha", type="password")
    
    if login_or_register == "Login":
        if st.button("Entrar"):
            user_data = login(email, senha)
            if user_data:
                st.session_state.user_id = user_data["user_id"]
                st.session_state.conversation_history = load_chat_history()
                st.success("Login realizado com sucesso!")
                st.experimental_rerun()
            else:
                st.error("Erro no login. Verifique suas credenciais.")
    
    elif login_or_register == "Cadastro":
        if st.button("Cadastrar"):
            user_id = create_account(email, senha)
            if user_id:

                st.success("Cadastro realizado com sucesso!")

            else:
                st.error("Erro ao criar a conta.")

# ------------------------------ RENDERIZAÇÃO PRINCIPAL --------------------------------------

if "user_id" not in st.session_state:
    login_or_register()
else:
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://img.icons8.com/?size=100&id=GjCK2f2wpZxt&format=png&color=000000", width=80)
    with col2:
        st.title("Chatbot Riot Valorant")
        st.caption("Faça perguntas sobre o melhor FPS existente!")

    with st.container(height=500, border=True):
        display_chat()

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Digite sua pergunta:", placeholder="Me fale sobre o Valorant.")
        submit_button = st.form_submit_button("Enviar ➤")

    if submit_button and user_input:
        with st.spinner("Buscando dados sobre Valorant..."):
            save_chat_message("user", user_input)
            st.session_state.conversation_history.append({
                "role": "user",
                "message": user_input,
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            resposta = generate_response(user_input)
            
            save_chat_message("assistant", resposta["text"], resposta["image_url"])
            st.session_state.conversation_history.append({
                "role": "assistant",
                "message": resposta["text"],
                "image_url": resposta["image_url"],
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            st.rerun()
    if st.button("Logout"):
        # Limpa o estado de sessão, efetivamente desconectando o usuário
        del st.session_state.user_id
        st.session_state.conversation_history = []  # Limpa o histórico de conversa
        st.success("Logout realizado com sucesso!")
        st.experimental_rerun()
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 0.9em; color: #666;' >
            Desenvolvido por Gildemberg Lopes, Kaíque Pereira e Maria Fernanda • Versão Valorant • {time.strftime('%d/%m/%Y')} 
        </div>
        """,
        unsafe_allow_html=True
    )
