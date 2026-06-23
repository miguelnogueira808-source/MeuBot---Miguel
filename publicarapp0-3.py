import streamlit as st
import google.generativeai as genai
import json
import os
import glob
import requests
from PIL import Image
import io
import base64

# --- CONFIGURAÇÃO ---
genai.configure(api_key="GOOGLE_API_KEY")
STABILITY_API_KEY = "STABILITY_API_KEY"

st.set_page_config(page_title="Meubot 0.3.1")
st.title("Meubot 0.3.1")

if not os.path.exists("historicos"):
    os.makedirs("historicos")

# --- FUNÇÕES ---
def salvar_conversa(nome, mensagens):
    with open(f"historicos/{nome}.json", "w") as f:
        json.dump(mensagens, f)

def carregar_mensagens(nome):
    path = f"historicos/{nome}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

# --- CSS PARA LIMPAR O VISUAL ---
st.markdown("""
    <style>
    div[data-testid="stSelectbox"] label { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
# --- BARRA LATERAL ---
# --- BARRA LATERAL ---
with st.sidebar:
    opcoes_modelos = {
        "Rapido": "models/gemini-3.1-flash-lite",
        "Simples": "models/gemini-3.5-flash",
        "Pro": "models/gemini-2.5-pro",
        "Gerador de Imagem": "stable-diffusion"
    }
    escolha_usuario = st.radio(
        "Escolha o modo:", 
        list(opcoes_modelos.keys()), 
        key="modo_selecionado"
    )
    modo = opcoes_modelos[escolha_usuario]

    nome_chat = st.text_input("Nova conversa:", placeholder="Nome...")
    if st.button("Criar Conversa") and nome_chat:
        salvar_conversa(nome_chat, [])
        st.rerun()

    conversa_selecionada = st.selectbox("", [""] + [f.replace("historicos/", "").replace(".json", "") for f in glob.glob("historicos/*.json")])
    
    escolha_usuario = st.radio(
        "Escolha o modo:", 
        list(opcoes_modelos.keys()), 
        key="modo_selecionado" # <--- Essa chave resolve o erro de duplicidade
    )

    nome_chat = st.text_input("Nova conversa:", placeholder="Nome...")
    if st.button("Criar Conversa") and nome_chat:
        salvar_conversa(nome_chat, [])
        st.rerun()

    conversa_selecionada = st.selectbox("", [""] + [f.replace("historicos/", "").replace(".json", "") for f in glob.glob("historicos/*.json")])
    escolha_usuario = st.radio("Escolha o modo:", list(opcoes_modelos.keys()))
    modo = opcoes_modelos[escolha_usuario]

    nome_chat = st.text_input("Nova conversa:", placeholder="Nome...")
    if st.button("Criar Conversa") and nome_chat:
        salvar_conversa(nome_chat, [])
        st.rerun()

    conversa_selecionada = st.selectbox("", [""] + [f.replace("historicos/", "").replace(".json", "") for f in glob.glob("historicos/*.json")])

# --- LÓGICA DO CHAT ---
    if conversa_selecionada:
    st.session_state.messages = carregar_mensagens(conversa_selecionada)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

       # Lógica de Imagem (Mudança para SDXL, mais amigável com a moderação)
    if modo == "stable-diffusion":
        with st.spinner("🎨 Gerando imagem..."):
            try:
                 # Endereço da API para SDXL v1.0
                 url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
                    
                 headers = {
                      "authorization": f"Bearer {STABILITY_API_KEY}",
                      "accept": "application/json", # Mudamos para JSON no SDXL
                      "content-type": "application/json"
                    }
                    
                    # Corpo da requisição ajustado para o formato do SDXL
                    json_data = {
                        "text_prompts": [{"text": prompt}],
                        "cfg_scale": 7,
                        "height": 1024,
                        "width": 1024,
                        "samples": 1,
                        "steps": 30,
                    }
                    
                    response = requests.post(url, headers=headers, json=json_data)
                    
                    if response.status_code == 200:
                        # O SDXL retorna a imagem em Base64 dentro do JSON
                        data = response.json()
                        img_base64 = data["artifacts"][0]["base64"]
                        img_data = io.BytesIO(base64.b64decode(img_base64))
                        img = Image.open(img_data)
                        st.image(img, caption=prompt)
                        st.session_state.messages.append({"role": "assistant", "content": f"Imagem: {prompt}"})
                        salvar_conversa(conversa_selecionada, st.session_state.messages)
                    else:
                        st.error(f"Erro na API: {response.text}")
                except Exception as e:
                    st.error(f"Erro: {e}")


else:
    st.info("Selecione uma conversa na barra lateral.")
