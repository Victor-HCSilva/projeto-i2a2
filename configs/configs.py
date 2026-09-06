# from componentes.tools.vectors.vector import VectorData
from decouple import config

from componentes.schemas.input_schemas import (
    GraphInput,
    ScatterInput,
    SearchDocumentInput,
    SQLDocumentInput,
    graph_tool,
    scatter_tool,
)
from componentes.utils.messages import messages

# Debug e mensagens
DEBUG = config("DEBUG", default=False, cast=bool)

m = None

try:
    from decouple import config
except ImportError:
    m = messages.Message()
    m.danger("Instale as dependências: pip install -r requirements.txt -U")

if DEBUG:
    msg = messages.Message()
    msg.danger("\n⚠️ Modo de depuração ativo.⚠️")

# Agent executor
RULES_PATH = config("RULES_PATH", default="./.files/rules/regras.txt")
RULES_PATCH = RULES_PATH
VERBOSE = True
HANDLE_PARSING_ERRORS = True

# Memory
RETURN_MESSAGE: bool = True
K = 5
MEMORY_KEY: str = "chat_history"

# LLM
llm_models = [
    "deepseek-coder:6.7b",  # 0
    "qwen3:latest",  # 1
    "gemini-pro",  # 2
    "gemini-2.0-flash",  # 3
    "mistral-small-latest",  # 4
]
MODEL = llm_models[4]
TEMPERATURE = 0.15
MAX_TOKENS = 500
EMBEDDING_MODEL = "nomic-embed-text"

# API KEYS
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default="NO_API_KEY")
if GOOGLE_API_KEY == "NO_API_KEY":
    raise ValueError("Defina a variável 'GOOGLE_API_KEY' no arquivo .env")

# PATHS
CSV_PATH_DIR = config("CSV_PATH_DIR", default="./.files/dataset/")
VECTOR_PATH = config("VECTOR_PATH", default="./vectors/data_vector")
RULES_PATH = config("RULES_PATH", default="./docs/regras.txt")
GRAFICO_PATH = config("GRAFICO_PATH", default="./.graph/grafico.html")
EW_DATASET_PATH = config("EW_DATASET_PATH", default="./.new-dataset.csv")

# Questions de teste
QUESTION1 = "./testes/questions/q1.txt"
QUESTION2 = "./testes/questions/q2.txt"
QUESTION3 = "./testes/questions/q3.txt"
QUESTION4 = "./testes/questions/q4.txt"

# ./configs/configs.py

import os
import shutil

import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_ollama import OllamaEmbeddings

# Importe PersistentVectorStore se for usar a abordagem de checar existências
# from langchain_community.vectorstores import Chroma # Já importado, mas reforçando


def create_vectorstore(
    csv_file_path: str = "./.files/dataset/dataset.csv",
    txt_file_path: str = "./.files/rules/regras.txt",
    chroma_db_path: str = "./chroma_db_agente_local",
    embeddings_model: str = "nomic-embed-text",
    force_recreate: bool = False,
):  # Adicionado parâmetro para forçar recriação
    """
    Cria ou carrega um vetorstore (ChromaDB) a partir de documentos de texto e CSV,
    e retorna o vetorstore e o DataFrame do dataset.

    Args:
        csv_file_path (str): Caminho para o arquivo CSV do dataset.
        txt_file_path (str): Caminho para o arquivo de regras em TXT.
        chroma_db_path (str): Caminho para o diretório onde o ChromaDB será persistido.
        embeddings_model (str): O nome do modelo de embeddings a ser usado (e.g., 'nomic-embed-text').
        force_recreate (bool): Se True, o ChromaDB será removido e recriado, mesmo que já exista.

    Returns:
        tuple: (vectorstore, df_info_dataset)
               - vectorstore: O objeto Chroma vetorstore.
               - df_info_dataset: O DataFrame pandas carregado do CSV.
    """

    print("DEBUG: Iniciando criação/carregamento do vetorstore e dataset.")

    # 1) Carregar os documentos de texto (regras.txt)
    if not os.path.exists(txt_file_path):
        print(f"ERRO: O arquivo de regras '{txt_file_path}' não foi encontrado.")
        return None, None

    loader = TextLoader(txt_file_path, encoding="utf-8")
    documents = loader.load()
    print(f"DEBUG: Documentos TXT carregados. Número de documentos: {len(documents)}")

    # Dividir documentos em chunks (pedaços menores)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    print(f"DEBUG: Número de chunks criados: {len(splits)}")
    if splits:
        print(f"DEBUG: Primeiro chunk: {splits[0].page_content[:100]}...")
    else:
        print("ALERTA: Nenhum chunk foi criado a partir dos documentos de texto.")

    # Inicializar o modelo de embeddings
    embeddings = OllamaEmbeddings(model=embeddings_model)

    # 2) Criação ou Carregamento do banco vetorial em chroma_db
    vectorstore = None

    # Lógica para remoção condicional
    if force_recreate and os.path.exists(chroma_db_path):
        print(
            f"DEBUG: Forçando recriação: Removendo diretório existente do ChromaDB: '{chroma_db_path}'"
        )
        shutil.rmtree(chroma_db_path)
        print("DEBUG: Diretório do ChromaDB removido com sucesso.")

    # Tenta carregar se o diretório existe e não está forçando a recriação
    if os.path.exists(chroma_db_path) and not force_recreate:
        print(f"DEBUG: Carregando ChromaDB existente de '{chroma_db_path}'...")
        try:
            vectorstore = Chroma(
                persist_directory=chroma_db_path, embedding_function=embeddings
            )
            print("DEBUG: ChromaDB existente carregado com sucesso!")
        except Exception as e:
            print(
                f"ERRO: Não foi possível carregar ChromaDB existente: {e}. Tentando recriar."
            )
            # Se der erro ao carregar, talvez o DB esteja corrompido, então remove e recria
            if os.path.exists(chroma_db_path):
                shutil.rmtree(chroma_db_path)
            print(
                "DEBUG: Criando e preenchendo novo ChromaDB com documentos atualizados..."
            )
            vectorstore = Chroma.from_documents(
                documents=splits, embedding=embeddings, persist_directory=chroma_db_path
            )
            print(
                "DEBUG: Novo ChromaDB criado e preenchido com sucesso com dados atualizados!"
            )
    else:
        print(
            "DEBUG: Criando e preenchendo novo ChromaDB com documentos atualizados..."
        )
        vectorstore = Chroma.from_documents(
            documents=splits, embedding=embeddings, persist_directory=chroma_db_path
        )
        print(
            "DEBUG: Novo ChromaDB criado e preenchido com sucesso com dados atualizados!"
        )

    # Teste: Contagem de Documentos
    if vectorstore:
        print(f"\nDEBUG: Número de chunks originais (splits): {len(splits)}")
        try:
            chroma_collection = vectorstore._collection
            count_in_db = chroma_collection.count()
            print(f"DEBUG: Número de documentos no ChromaDB: {count_in_db}")

            if count_in_db == len(splits):
                print(
                    "DEBUG: A contagem de documentos no ChromaDB corresponde ao número de splits."
                )
            else:
                print(
                    "ALERTA: A contagem de documentos no ChromaDB NÃO corresponde ao número de splits. Pode haver um problema."
                )
        except Exception as e:
            print(f"ERRO: Não foi possível contar documentos no ChromaDB: {e}")

    # 3) Carregar o dataset CSV
    df_info_dataset = None
    try:
        df_info_dataset = pd.read_csv(csv_file_path)
        print(
            f"DEBUG: Dataset CSV carregado em DataFrame. Linhas: {len(df_info_dataset)}"
        )
    except FileNotFoundError:
        print(f"ERRO: O arquivo '{csv_file_path}' não foi encontrado.")
    except Exception as e:
        print(f"ERRO: Não foi possível carregar o CSV para DataFrame: {e}")

    return vectorstore, df_info_dataset


def build_tools(vectorstore, csv_path: str):
    from componentes.utils.utils.utils import document_sql, get_csv

    TOOLS = [
        {
            "sql_doc": lambda query_sql: document_sql(query_sql, get_csv(csv_path)),
            "search_doc": "Consulta SQL no dataset",
            "search_doc_input": "query_tool",
            "function_schema": SQLDocumentInput,
        },
        {
            "sql_doc": lambda query: vectorstore.as_retriever().invoke(query),
            "search_doc": "Busca nos documentos",
            "search_doc_input": "buscar_tool",
            "function_schema": SearchDocumentInput,
        },
        {
            "sql_doc": graph_tool,
            "search_doc": "Gera gráficos a partir de dados",
            "search_doc_input": "graph_tool",
            "function_schema": GraphInput,
        },
        {
            "sql_doc": scatter_tool,
            "search_doc": "Gera gráfico de dispersão a partir dos dados",
            "search_doc_input": "scatter_tool",
            "function_schema": ScatterInput,
        },
    ]
    return TOOLS


if __name__ == "__main__":
    vs, df = create_vectorstore()
    print("vectorstore:", type(vs), "df rows:", None if df is None else len(df))
