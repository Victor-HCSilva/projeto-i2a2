#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
print(sys.executable)


# In[2]:


#Bibliotecas do agente 
from langchain_ollama import OllamaLLM
from langchain.agents import initialize_agent, AgentType, AgentExecutor # Usado para os sub-agentes
from langchain_core.tools import StructuredTool # Para ferramentas com schema
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory # Importação da memória / definição de contexto para armazenamento da memória
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder # Para o agente principal

# Necessário para StructuredTool
from langchain_core.messages import HumanMessage, AIMessage 

# model
from pydantic import BaseModel, Field

#Funções diversas em Python
import os
import pandas as pd
from pandasql import sqldf
import matplotlib.pyplot as plt
import re

#importações para RAG
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma #banco vetorial
import shutil 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings




# In[3]:


#1) Criação da pasta onde estão as informações
docs_folder = "docs"
csv_file_path = os.path.join(docs_folder, "dataset.csv")
txt_file_path = os.path.join(docs_folder, "regras.txt")

#carregar os documentos
loader = TextLoader(txt_file_path, encoding="utf-8")
documents = loader.load()
print(f"DEBUG: Documentos carregados. Número de documentos: {len(documents)}")

# Dividir documentos em chunks (pedaços menores)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(documents)
print(f"DEBUG: Número de chunks criados: {len(splits)}")
print(f"DEBUG: Primeiro chunk: {splits[0].page_content[:100]}...")

embeddings_model = 'nomic-embed-text'
embeddings = OllamaEmbeddings(model=embeddings_model)


# In[4]:


# 2) Criação ou Carregamento do banco vetorial em chroma_db
# Definindo um caminho de pasta específico para este projeto
chroma_db_path = "./chroma_db_agente_local" 
vectorstore = None # Inicializa o vectorstore como None

if os.path.exists(chroma_db_path):
    print(f"DEBUG: Removendo diretório existente do ChromaDB para forçar atualização: '{chroma_db_path}'")
    shutil.rmtree(chroma_db_path)
    print("DEBUG: Diretório do ChromaDB removido com sucesso.")

print("DEBUG: Criando e preenchendo novo ChromaDB com documentos atualizados...")
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory=chroma_db_path
)
print("DEBUG: Novo ChromaDB criado e preenchido com sucesso com dados atualizados!")

# teste. Contagem de Documentos
print(f"\nDEBUG: Número de chunks originais (splits): {len(splits)}")
try:
    chroma_collection = vectorstore._collection
    count_in_db = chroma_collection.count()
    print(f"DEBUG: Número de documentos no ChromaDB: {count_in_db}")

    if count_in_db == len(splits):
        print("DEBUG: A contagem de documentos no ChromaDB corresponde ao número de splits.")
    else:
        print("ALERTA: A contagem de documentos no ChromaDB NÃO corresponde ao número de splits. Pode haver um problema.")
except Exception as e:
    print(f"ERRO: Não foi possível contar documentos no ChromaDB: {e}")


# In[5]:


#3) Criação de funções

#criação do dataset
df_info_dataset = None
try:
    df_info_dataset = pd.read_csv(csv_file_path)
    print(f"DEBUG: Dataset CSV carregado em DataFrame. Linhas: {len(df_info_dataset)}")
except FileNotFoundError:
    print(f"ERRO: O arquivo '{csv_file_path}' não foi encontrado.")
except Exception as e:
    print(f"ERRO: Não foi possível carregar o CSV para DataFrame: {e}")


def buscar_documentos (query: str) -> str:
    """**PRIMEIRA ETAPA SEMPRE**
    utilize essa ferramenta sempre no inicio da query para interpretar e entender as regras de negócio da pergunta do usuário.
    essa ferramenta aceita a query em linguagem natural.
    """
    
    
    retriever = vectorstore.as_retriever()
    docs = retriever.invoke(query)
    if docs:
        return "\n\n".join([doc.page_content for doc in docs])
    else:
        return "Não encontrei informações relevantes nos documentos para esta consulta."
    
def sql_documentos (query_sql: str) -> str:
    """
    ** SEGUNDA ETAPA SEMPRE**
    Use esta ferramenta para **consultas quantitativas/qualitativas** dentro do dataset chamado 'df_info_dataset'
    Esta ferramenta exige uma query onde o 'from' deve ser sempre 'df_info_dataset
    """
    
    global df_info_dataset # Permite que a função acesse o df_data global
    if df_info_dataset is None:
        return "Erro: O DataFrame 'df_info_dataset' não foi carregado. Não é possível executar consultas SQL."

    colunas_originais = df_info_dataset.columns.tolist()
    
    # Cria dicionário de mapeamento simples
    mapeamento = {}
    for col in colunas_originais:
        col_nova = col.upper()
        col_nova = re.sub(r"[^A-Z0-9]", "_", col_nova)  # Substitui espaços/símbolos por _
        col_nova = re.sub(r"_+", "_", col_nova).strip("_")  # Remove múltiplos _
        mapeamento[col] = col_nova

    # Aplica o mapeamento
    df_info_dataset.columns = [mapeamento[col] for col in df_info_dataset.columns]
    

    result = sqldf(query_sql, {'df_info_dataset': df_info_dataset}) # Mapeamento do dataset para o agente

   
    if not result.empty and len(result.columns) == 1 and len(result) == 1:
        return str(result.iloc[0, 0]) # Retorna o valor da única célula como string
    else:
        return result.to_string(index=False)


# In[6]:


#4) Criação de Schema
class buscar_documentos_input(BaseModel):
    query: str = Field(description="Consulta na documentaçao.")

class sql_documentos_input(BaseModel):
    query_sql: str = Field(description="Consulta SQL no dataset df_info_dataset")


# In[7]:


#5) Criação das ferramentas estruturadas
buscar_tool = StructuredTool.from_function(
    func=buscar_documentos,
    name='buscar_documentos',
    description=buscar_documentos.__doc__.strip(),
    args_schema=buscar_documentos_input
)

query_tool = StructuredTool.from_function(
    func=sql_documentos,
    name='sql_documentos',
    description=sql_documentos.__doc__.strip(),
    args_schema=sql_documentos_input
)


# In[8]:


#6) Criação da memória dos agentes
main_memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    return_messages=True,
    k=5 # Mantenha as últimas 5 interações (5 pares de HumanMessage/AIMessage)
)


# In[9]:


#7) Criação do Agente
llm = OllamaLLM(model="deepseek-coder:6.7b",
                temperature=0.15,
                max_tokens=500
                )

agent_executor = initialize_agent(
    tools=[query_tool, buscar_tool],
    llm=llm,
    agent_type=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    memory=main_memory, # Adicionando memória
    agent_kwargs={"system_message": """Você é um analista de dados focado em trazer os resultados de projetos.
    Sempre utilize as ferramentas disponíveis para responder às perguntas do usuário.

    **IMPORTANTE: Seu processo de pensamento deve seguir o formato ReAct (Thought, Action, Action Input, Observation, Thought, Final Answer).**

    **Regras de Uso das Ferramentas:**
                                
    1.  SEMPRE SIGA O SEGUINTE FLUXO: I. buscar_tool (para entendimento das regras de negócio) -> II. query_tool (para confecçao da query quantitativa/qualitativa),
                        
        **Para perguntas de caráter quantitativo ou qualitativo que exigem análise de dados tabulares, agregação (COUNT, SUM, AVG), filtragem precisa ou qualquer cálculo sobre o dataset, VOCÊ DEVE usar a ferramenta 'query_tool'. Lembre-se que o nome da tabela no SQL é 'df_info_dataset'.**
        * Ao usar a 'query_tool', o **Action Input DEVE CONTER APENAS a string SQL pura e NADA MAIS**.
        * **NÃO INCLUA ASPAS TRIPLAS (```) OU QUALQUER OUTRO DELIMITADOR DE CÓDIGO NO Action Input para 'query_tool'.**
        * **EXEMPLO CERTO:** Action Input: SELECT MARCA, SUM(CPV_UND) FROM df_info_dataset GROUP BY MARCA
        * **EXEMPLO ERRADO:** Action Input: ```SELECT MARCA, SUM(CPV_UND) FROM df_info_dataset GROUP BY MARCA```
                  
        **Regras Específicas para Filtros de Data:**
        * Ao filtrar por datas, **SEMPRE** utilize o formato `WHERE DATA >= 'YYYY-MM-DD' AND DATA <= 'YYYY-MM-DD'`.
        * **NUNCA** utilize funções como `year(DATA) = YYYY` ou `month(DATA) = MM` ou qualquer outro método que não seja a comparação direta de datas no formato 'YYYY-MM-DD'.
        * **EXEMPLO CERTO DE FILTRO DE DATA:** `WHERE DATA >='2025-05-01' AND DATA <= '2024-05-31'` 
        * **EXEMPLO ERRADO DE FILTRO DE DATA:** `WHERE year(DATA) = 2024 AND month(DATA) = 5`
                   
        * Exemplo de Thought para esta ferramenta: "A pergunta é quantitativa, preciso usar query_tool para contar as marcas."
        * Exemplo de Final Answer após usar esta ferramenta: "Existem X marcas no dataset."
                            
    """
}

)
print("DEBUG: Agente configurado com sucesso para LLM local.")


# In[ ]:


# 8) Testando o agente
chat_history = []

print("\n--- Teste 1: Pergunta 1 ---")
user_input_1 = "Quantas Marcas existem neste arquivo?"
response_1 = agent_executor.invoke({"input": user_input_1, "chat_history": chat_history})
chat_history.extend([HumanMessage(content=user_input_1), AIMessage(content=response_1["output"])])
print(f"Resposta: {response_1['output']}\n")


# In[ ]:


print("\n--- Teste 2: Pergunta de cálculo ---")
user_input_2 = "Considerando o total de unidades CPV, qual foi a marca que mais vendeu?"
response_2 = agent_executor.invoke({"input": user_input_2, "chat_history": chat_history})
chat_history.extend([HumanMessage(content=user_input_2), AIMessage(content=response_2["output"])])
print(f"Resposta: {response_2['output']}\n")


# In[ ]:


print("\n--- Teste 3: Pergunta sobre documentos ---")
user_input_3 = "Qual a terceira maior marca vendido em maio de 2024?"
response_3 = agent_executor.invoke({"input": user_input_3, "chat_history": chat_history})
chat_history.extend([HumanMessage(content=user_input_3), AIMessage(content=response_3["output"])])
print(f"Resposta: {response_3['output']}\n")


# In[ ]:


print("\n--- Teste 4: Outra pergunta sobre documentos ---")
user_input_4 = "Me diga a conversão da Marca NUBERON em agosto de 2024"
response_4 = agent_executor.invoke({"input": user_input_4, "chat_history": chat_history})
chat_history.extend([HumanMessage(content=user_input_4), AIMessage(content=response_4["output"])])
print(f"Resposta: {response_4['output']}\n")

