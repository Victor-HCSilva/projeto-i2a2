import os
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Use o mesmo modelo que você está configurando para embeddings
# Se você está usando MODEL = 'qwen3:latest' no configs, use-o aqui.
# Se você seguiu minha sugestão e criou EMBEDDING_MODEL = 'nomic-embed-text', use nomic-embed-text aqui.
EMBEDDING_MODEL_NAME = 'qwen3:latest' # <-- AJUSTE AQUI SE VOCÊ ESTIVER USANDO OUTRO MODELO PARA EMBEDDINGS

# Caminho para o seu arquivo de regras
RULES_FILE_PATH = './docs/regras.txt'

def read_archive(file_path):
    """Função para ler o arquivo, similar à sua utils.utils.read_archive"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {file_path}")
        return ""
    except Exception as e:
        print(f"ERRO: Não foi possível ler o arquivo {file_path}: {e}")
        return ""

print(f"--- Teste de Embeddings com o modelo: {EMBEDDING_MODEL_NAME} ---")

# 1. Carregar o documento
document_content = read_archive(RULES_FILE_PATH)

if not document_content.strip():
    print("ERRO: O conteúdo do arquivo de regras está vazio. Verifique o arquivo.")
    exit(1)

print(f"Conteúdo do arquivo lido (primeiros 100 caracteres): {document_content[:100]}...")

# 2. Criar um objeto Document
documents = [Document(page_content=document_content)]
print(f"Número de objetos Document iniciais: {len(documents)}")

# 3. Dividir o documento em chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(documents)

if not splits:
    print("ERRO: Nenhum chunk foi gerado após a divisão do documento. O documento pode ser muito pequeno ou vazio.")
    exit(1)

print(f"Número de chunks gerados: {len(splits)}")
print(f"Primeiro chunk (primeiros 100 caracteres): {splits[0].page_content[:100]}...")

# 4. Tentar carregar o modelo de embeddings
try:
    print(f"Tentando carregar o modelo OllamaEmbeddings: {EMBEDDING_MODEL_NAME}...")
    embeddings_model = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)
    print("Modelo OllamaEmbeddings carregado com sucesso.")
except Exception as e:
    print(f"ERRO: Não foi possível carregar o modelo OllamaEmbeddings '{EMBEDDING_MODEL_NAME}': {e}")
    print("Causas prováveis: Ollama não está rodando, o modelo não está instalado, ou nome do modelo está incorreto.")
    exit(1)

# 5. Gerar embeddings para um chunk de teste
try:
    print(f"Gerando embeddings para o primeiro chunk de texto...")
    test_text = splits[0].page_content
    test_embedding = embeddings_model.embed_query(test_text)

    if not test_embedding:
        print("ERRO: A lista de embeddings retornada está vazia (`[]`).")
        print(f"Isso significa que o modelo '{EMBEDDING_MODEL_NAME}' não conseguiu gerar embeddings para o texto fornecido.")
        print("Causas: O modelo pode não ser projetado para embeddings, ou há um problema interno do Ollama.")
        exit(1)

    print(f"Embedding gerado com sucesso! Tamanho do embedding: {len(test_embedding)}")
    print(f"Primeiros 10 valores do embedding: {test_embedding[:10]}")

except Exception as e:
    print(f"ERRO: Falha ao gerar embeddings: {e}")
    print("Verifique a conexão com o Ollama e se o modelo está funcionando corretamente para embeddings.")
    exit(1)

print("\n--- Teste de Embeddings CONCLUÍDO com sucesso (ou com erro específico acima) ---")
