from decouple import config
import streamlit as st
from componentes.main.main import init_agent
from langchain_core.messages import HumanMessage, AIMessage
import os

# ----------------------------
# Inicializa o agente
# ----------------------------
agent_executor, memory = init_agent()
chat_history = []

st.title("Teste da Ferramenta de Gráficos do Agente 📊🤖")

# Entrada de teste
user_input = st.text_input("Digite a pergunta para o agente:")

if st.button("Executar"):
    if not user_input.strip():
        st.warning("Por favor, digite uma pergunta.")
    else:
        # Chama o agente
        st.write(
            "Aguarde, Agente pensando☝️🤓..."
        )
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })

        # Atualiza histórico
        chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=response["output"])
        ])

        # Mostra resposta textual
        st.subheader("Resposta do agente")
        st.write(response["output"])

        # Exibe gráfico gerado (HTML)
        graph_path =config("GRAFICO_PATH")
        if os.path.exists(graph_path):
            st.subheader("Gráfico gerado")
            with open(graph_path, "r") as f:
                st.components.v1.html(f.read(), height=500)
        else:
            st.info("Nenhum gráfico foi gerado. Certifique-se de que a pergunta requer gráficos.")
