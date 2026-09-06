import os
import streamlit as st

class SaveFiles:
    def save_file(self, path: str, uploaded_file):
        # Cria os diretórios do caminho, mas não o arquivo
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Salva o arquivo
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return f"Arquivo salvo com sucesso em {path}"
