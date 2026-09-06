import os
from typing import Callable, Union, Type
from langchain_ollama import OllamaLLM  # Mantido apenas como referência
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import initialize_agent, AgentType
from langchain_core.messages import HumanMessage, AIMessage
from componentes.utils.utils.utils import read_archive
from componentes.tools.structured_tools.structured_tools import ManagerTools
from configs.configs import (
    RULES_PATCH,
    VERBOSE,
    HANDLE_PARSING_ERRORS,
    RETURN_MESSAGE,
    K,
    MEMORY_KEY,
    MODEL,            # Nome do modelo (gemini-pro, mistral-small-latest, etc.)
    TEMPERATURE,
    MAX_TOKENS,
)
# from decouple import config # <-- REMOVIDO
from componentes.utils.messages.messages import Message as MSG
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from openai import OpenAI
import streamlit as st # <-- Adicionado para st.secrets

# --- Config API Keys ---
# Estas variáveis de ambiente deveriam ser definidas pelo Streamlit Cloud/local secrets.toml
# Removi as chamadas a config() aqui, pois elas serão acessadas via st.secrets
# os.environ["OPENAI_API_KEY"] e os.environ["OPENAI_API_BASE"] são geralmente configuradas
# automaticamente pelo LangChain se ChatOpenAI for usado e a API key for passada diretamente.
# Caso contrário, você pode configurá-las com os valores de st.secrets se necessário.
# Por enquanto, vou remover as atribuições diretas de os.environ e confiar no LangChain.

# --- Modelo/Provedor escolhido ---
# Este ainda precisa ser obtido de algum lugar. Se for uma configuração do Streamlit,
# também precisaria vir de st.secrets.
# Por enquanto, vou manter como uma variável, mas o ideal seria passá-lo também.
# Para este exemplo, vou assumir que 'MODEL_PROVIDER' pode ser definido no 'secrets.toml'
# ou passado como argumento para init_agent.
# Se for um valor fixo, pode ser definido diretamente aqui.
MODEL_PROVIDER = st.secrets.get("MODEL_PROVIDER", "gemini") # <-- Assume que MODEL_PROVIDER está nos secrets

# --- Factory Tools ---
def factory_tools(tools: list[dict[str, Union[str, Callable, Type]]]) -> list:
    """
    Cria instâncias de ManagerTools a partir de uma lista de dicionários.
    """
    all_tools = []
    for tool in tools:
        # print(f"Tool: {tool}") # Removido para evitar poluição no console, pode ser reativado para debug
        all_tools.append(ManagerTools(**tool).get_tool())
    return all_tools


# --- Inicialização condicional do agente ---
# Adicionado 'streamlit_secrets' como argumento para passar o objeto st.secrets
def init_agent(tools: list[dict], streamlit_secrets: dict) -> tuple:
    """
    Inicializa o agente com as ferramentas fornecidas dinamicamente.
    """
    memory = ConversationBufferWindowMemory(
        memory_key=MEMORY_KEY,
        return_messages=RETURN_MESSAGE,
        k=K
    )

    # Cria instâncias de ferramentas
    tools_list = factory_tools(tools)

    # Seleção do modelo
    if MODEL_PROVIDER.lower() == "gemini":
        gemini_api_key = streamlit_secrets.get('GOOGLE_API_KEY')
        if not gemini_api_key:
            raise ValueError("GOOGLE_API_KEY não encontrada nos secrets do Streamlit para o provedor Gemini.")
        genai.configure(api_key=gemini_api_key)
        llm = ChatGoogleGenerativeAI(
            model=MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            convert_system_message_to_human=True,
            google_api_key=gemini_api_key # Já configurado acima, mas bom passar para o ChatGoogleGenerativeAI
        )

    elif MODEL_PROVIDER.lower() == "mistral":
        mistral_api_key = streamlit_secrets.get("MISTRAL_API_KEY")
        mistral_base_url = streamlit_secrets.get("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")

        if not mistral_api_key:
            raise ValueError("MISTRAL_API_KEY não encontrada nos secrets do Streamlit para o provedor Mistral.")

        # O cliente OpenAI da biblioteca 'openai' pode ser útil para outras operações,
        # mas o ChatOpenAI do LangChain é o que importa aqui para o LLM.
        # Ele automaticamente usa a API key e base URL se passadas como argumentos.
        # client = OpenAI(
        #     base_url=mistral_base_url,
        #     api_key=mistral_api_key
        # )

        # Wrapper para LangChain (importação pode ser local para evitar conflitos se não usado)
        from langchain_openai import ChatOpenAI # Usando langchain_openai para Mistral, como no código anterior
        llm = ChatOpenAI(
            model=MODEL, # Renomeado de model_name para model para consistência
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            api_key=mistral_api_key, # Passa a chave diretamente
            base_url=mistral_base_url # Passa a base URL diretamente
        )

    else:
        raise ValueError(f"MODEL_PROVIDER inválido: {MODEL_PROVIDER}")

    agent_executor = initialize_agent(
        tools=tools_list,
        llm=llm,
        agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=VERBOSE,
        handle_parsing_errors=HANDLE_PARSING_ERRORS,
        memory=memory,
        agent_kwargs={"system_message": read_archive(RULES_PATCH, 'r')},
        max_iterations=streamlit_secrets.get("MAX_ITERATIONS", 20) # <-- Usando st.secrets para MAX_ITERATIONS
    )

    return agent_executor, memory


# --- Função principal ---
def run_agent(user_input: str, agent_executor, chat_history: list) -> str:
    if not user_input.strip():
        return "Digite alguma pergunta ou consulta SQL."

    response = agent_executor.invoke({
        "input": user_input,
        "chat_history": chat_history
    })

    chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=response["output"])
    ])

    return response["output"]


# --- Execução de teste ---
if __name__ == '__main__':
    # Simulação de st.secrets para o bloco de teste
    # No seu app Streamlit real, você passaria st.secrets diretamente.
    # Aqui, criamos um dicionário mock.
    mock_secrets = {
        "MISTRAL_API_KEY": os.getenv("MISTRAL_API_KEY_TEST", "your_mistral_test_key"),
        "MISTRAL_BASE_URL": os.getenv("MISTRAL_BASE_URL_TEST", "https://api.mistral.ai/v1"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY_TEST", "your_gemini_test_key"),
        "MODEL_PROVIDER": os.getenv("MODEL_PROVIDER_TEST", "mistral"), # Pode ser 'gemini' para testar
        "MAX_ITERATIONS": 20,
        "QUESTION1": "Mostre as 5 primeiras linhas do dataframe." # Adicionei uma pergunta de exemplo
    }
    # Para o teste, usamos os.getenv para permitir sobrescrever via ambiente, mas fallback para mock
    # Você precisaria ter as variáveis de ambiente setadas para o teste ou usar valores hardcoded para mock.

    from configs.configs import build_tools, vectorize_data, CSV_PATH_DIR
    from componentes.utils.utils.utils import search_archive

    # Teste rápido com dataset se existir
    csv_path = search_archive(CSV_PATH_DIR)
    if not csv_path:
        print("Nenhum CSV encontrado para teste.")
    else:
        vectorstore = vectorize_data(csv_path)
        tools = build_tools(vectorstore, csv_path)

        chat_history = []
        # Passando o dicionário mock_secrets para init_agent
        agent_executor, _ = init_agent(tools, mock_secrets)
        print(run_agent(read_archive(mock_secrets['QUESTION1']), agent_executor, chat_history))
