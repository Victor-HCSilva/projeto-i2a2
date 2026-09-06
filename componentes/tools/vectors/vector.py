import os
import shutil
from google.auth import default
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma  # banco vetorial
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from componentes.utils.messages import messages
from decouple import config
from configs import configs

if config('DEBUG', default=False):
    m = messages.Message()

class VectorData:
    def __init__(
        self,
        path: str,
        documents,
        agent_name: str
    ) -> None:
        self.path = path
        self.documents = documents
        self.agent_name = agent_name
        self.params = {
            "Caminho":self.path,
            "Agente": self.agent_name,
            "Document":self.documents,
        }

    def split_prompt(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(
            self.documents
        )

    #def delete_old_vector_data_(self):
    #    if os.path.exists(self.path):
    #        shutil.rmtree(self.path)

    def create_vector(self):
        print("Documents:", self.documents)
        print("Split documents:", self.split_prompt())
        print("Embedding model:", self.agent_name)
        print("Vector path:", self.path)

        try:
            vector = Chroma.from_documents(
                documents=self.split_prompt(),
                embedding=self.get_embeddings_models(),
                persist_directory=self.path
            )
            self.size_vector = vector._collection.count()
            return vector
        except Exception as e:
            print(f"ERRO: Falha ao criar o banco vetorial: {e}")
            return None


    def get_embeddings_models(self):
        try:
            return OllamaEmbeddings(model=self.agent_name)
        except Exception as e:
            if configs.DEBUG:
                m.danger(f"Erro ao carregar agente {self.agent_name}: {e}")
            # Adicione um print e relance a exceção ou retorne None
            print(f"ERRO: Falha ao carregar o modelo de embeddings {self.agent_name}: {e}")
            raise # Importante relançar para que o chamador saiba que falhou
            # Ou: return None e tratar no create_vector

    def get_size_split(self):
        docs_split = self.split_prompt()
        return len(docs_split) if docs_split else 0

    def get_size_chunks(self) -> int:
        try:
            return self.size_vector
        except Exception as e:
            if configs.DEBUG:
                m.danger(
                    f"erro ao pegar tamanho do vetor {e}"
                )
            return 0

    def check_size(self) -> bool:
        return self.get_size_chunks() == self.get_size_split()

    def info_size(self):
        local_m = messages.Message()
        if self.check_size():
            local_m.very_safe(
            f"""
              Quantidade de Chunks iguais a dos Splits:\n
              Split(s): {self.get_size_split()}\n
              Chunk(s): {self.get_size_chunks()}
            """
            )
            return
        local_m.warning(
         f"""
          Quantidade de Chunks diferentes dos Splits:\n
          Split(s): {self.get_size_split()}\n
          Chunk(s): {self.get_size_chunks()}
        """
        )

        if configs.DEBUG:
            for k, v in self.params.items():
                m.any_color(
                    f"parametros:\n{k}: {v}",
                    "verde"
                )
