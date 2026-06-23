import streamlit as st
import google.generativeai as genai
import json
import os
import glob
import requests
import base64
from PIL import Image
import io

# --- CONFIGURAÇÃO ---
# As chaves agora serão lidas do Secrets do Streamlit
st.set_page_config(page_title="Meubot 0.3.1")
st.title("Meubot 0.3.1")

if not os.path.exists("historicos"):
    os.makedirs("historicos")

def salvar_conversa(nome, mensagens):
    with open(f"historicos/{nome}.json", "w") as f:
        json.dump(mensagens, f)

def carregar_mensagens(nome):
    path = f"historicos/{nome}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

# --- BARRA LATERAL ---
with st.sidebar:
    opcoes_modelos = {
        "Rapido": "models/gemini-3.1-flash-lite",
        "Simples": "models/gemini-3.5-flash",
        "Pro": "models/gemini-2.5-pro",
        "Imagem": "stable-diffusion"
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

# --- LÓGICA DO CHAT ---
if conversa_selecionada:
    st.session_state.messages = carregar_mensagens(conversa_selecionada)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        if modo == "stable-diffusion":
            with st.spinner("🎨 Gerando imagem..."):
                url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
                # Lendo a chave de forma segura
                headers = {"authorization": f"Bearer {st.secrets['STABILITY_API_KEY']}", "accept": "application/json"}
                json_data = {"text_prompts": [{"text": prompt}], "cfg_scale": 7, "height": 1024, "width": 1024, "samples": 1, "steps": 30}
                response = requests.post(url, headers=headers, json=json_data)
                if response.status_code == 200:
                    img_base64 = response.json()["artifacts"][0]["base64"]
                    img = Image.open(io.BytesIO(base64.b64decode(img_base64)))
                    st.image(img, caption=prompt)
                    st.session_state.messages.append({"role": "assistant", "content": f"Imagem: {prompt}"})
                    salvar_conversa(conversa_selecionada, st.session_state.messages)
        else:
            # Lendo a chave de forma segura
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            model = genai.GenerativeModel(modo)
            response = model.generate_content(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.chat_message("assistant").markdown(response.text)
            salvar_conversa(conversa_selecionada, st.session_state.messages)

