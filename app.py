import logging
import os

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans

from configs.runtime_config import get_llm_config

# ======================
# CONFIGURAÇÕES E LOGS
# ======================
GRAFICO_PATH = "./grafico.html"
MAX_LINHAS_AMOSTRA = 100

LOG_DIR = "./.log"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "log.txt")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

# ======================
# FUNÇÕES DE ANÁLISE
# ======================


def descrever_dados(df: pd.DataFrame) -> str:
    """Gera um resumo estatístico e informações gerais sobre o DataFrame."""
    info = {
        "num_linhas": len(df),
        "num_colunas": len(df.columns),
        "colunas": list(df.columns),
        "tipos": df.dtypes.astype(str).to_dict(),
    }
    return str(info)


def identificar_padroes(df: pd.DataFrame) -> str:
    """Identifica padrões e clusters básicos nos dados numéricos."""
    num_df = df.select_dtypes(include="number").dropna()
    if len(num_df.columns) >= 2 and len(num_df) > 5:
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        labels = kmeans.fit_predict(num_df.head(1000))
        return (
            f"Clusters detectados: {dict(zip(*np.unique(labels, return_counts=True)))}"
        )
    return "Dados insuficientes para padrões complexos."


# ======================
# FERRAMENTA DE GRÁFICO
# ======================


class GraficoInput(BaseModel):
    tipo: str = Field(description="Tipo de gráfico: barras, linha, pontos ou pizza")
    x: str = Field(description="Nome da coluna para o eixo X")
    y: str = Field(description="Nome da coluna para o eixo Y")


def gerar_grafico_exec(tipo: str, x: str, y: str) -> str:
    """Gera um gráfico visual. Use esta ferramenta apenas quando solicitado um gráfico."""
    try:
        df = st.session_state.df_session
        df_plot = df.head(MAX_LINHAS_AMOSTRA)
        tipo = tipo.lower()

        if tipo == "barras":
            fig = px.bar(df_plot, x=x, y=y, title=f"{x} vs {y}")
        elif tipo == "linha":
            fig = px.line(df_plot, x=x, y=y, title=f"{x} vs {y}")
        elif tipo == "pontos":
            fig = px.scatter(df_plot, x=x, y=y, title=f"{x} vs {y}")
        elif tipo == "pizza":
            fig = px.pie(df_plot, names=x, values=y, title=f"{x} vs {y}")
        else:
            return f"Tipo de gráfico '{tipo}' não suportado."

        fig.write_html(GRAFICO_PATH)
        return f"✅ Gráfico de {tipo} gerado com sucesso entre {x} e {y}. Salvo em {GRAFICO_PATH}"
    except Exception as e:
        logging.exception(f"Erro na geração do gráfico ({tipo}, x={x}, y={y})")
        return f"❌ Erro ao gerar gráfico: {str(e)}"


# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Agente de Análise de CSV (Gemini)", layout="wide")
st.title("📊 Agente de Análise de CSV (Gemini + Streamlit)")

uploaded_file = st.file_uploader("Upload do arquivo CSV", type=["csv"])

if uploaded_file:
    if (
        "df_session" not in st.session_state
        or st.session_state.get("filename") != uploaded_file.name
    ):
        st.session_state.df_session = pd.read_csv(uploaded_file)
        st.session_state.filename = uploaded_file.name
        st.session_state.messages = []
        if os.path.exists(GRAFICO_PATH):
            os.remove(GRAFICO_PATH)

    df = st.session_state.df_session
    st.write("### Prévia dos dados")
    st.dataframe(df.head(10))

    llm_config = get_llm_config()
    provider_name = llm_config.get("provider")
    api_key = llm_config.get("api_key")
    model_name = llm_config.get("model")

    if not api_key:
        st.error(
            "🔑 Nenhuma chave de API válida foi encontrada. configure GEMINI_API_KEY/GOOGLE_API_KEY "
            "ou a variável de ambiente equivalente antes de usar o agente."
        )
        st.stop()

    if provider_name != "gemini":
        st.warning(
            f"Provedor configurado: {provider_name}. Este app foi validado com Gemini e usará o modelo configurado do provedor atual."
        )

    llm = ChatGoogleGenerativeAI(
        model=model_name or "gemini-3.6-flash",
        api_key=api_key,
        temperature=0,
        disable_streaming="tool_calling",
    )

    # DEFINIÇÃO DE FERRAMENTAS
    tools = [
        StructuredTool.from_function(
            func=lambda: descrever_dados(df),
            name="descrever_dados",
            description="Retorna informações sobre colunas e linhas do arquivo.",
            return_direct=True,
        ),
        StructuredTool.from_function(
            func=lambda: identificar_padroes(df),
            name="identificar_padroes",
            description="Analisa clusters e padrões nos dados.",
            return_direct=True,
        ),
        StructuredTool.from_function(
            func=gerar_grafico_exec,
            name="gerar_grafico",
            description="Cria gráficos (barras, linha, pontos ou pizza) informando x e y.",
            args_schema=GraficoInput,
            return_direct=True,
        ),
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"Você é um analista de dados experiente. Colunas disponíveis: {list(df.columns)}. Responda sempre em Português de forma clara e objetiva.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        ),
    )

    # Exibição do histórico de mensagens
    for message_index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if (
                message["role"] == "assistant"
                and "✅ Gráfico" in message["content"]
                and os.path.exists(GRAFICO_PATH)
            ):
                with open(GRAFICO_PATH, "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=500, scrolling=True)
                st.download_button(
                    "Baixar Gráfico",
                    open(GRAFICO_PATH, "rb"),
                    file_name="grafico.html",
                    key=f"download_grafico_historico_{message_index}",
                )

    if pergunta := st.chat_input(
        "Ex: Crie um gráfico de barras das colunas data e vendas_ocorridas"
    ):
        st.session_state.messages.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Analisando dados..."):
                try:
                    resposta = agent_executor.invoke({"input": pergunta})
                    output = resposta["output"]
                    st.markdown(output)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": output}
                    )

                    if os.path.exists(GRAFICO_PATH) and "✅ Gráfico" in output:
                        with open(GRAFICO_PATH, "r", encoding="utf-8") as f:
                            st.components.v1.html(f.read(), height=500, scrolling=True)
                        st.download_button(
                            "Baixar Gráfico",
                            open(GRAFICO_PATH, "rb"),
                            file_name="grafico.html",
                            key="download_grafico_atual",
                        )
                except Exception as e:
                    # Registra no ./.log/log.txt o erro com traceback completo
                    logging.exception(
                        f"Erro ao processar a pergunta: '{pergunta}'\nErro: {e}"
                    )
                    st.error("Erro ao processar 💀")
