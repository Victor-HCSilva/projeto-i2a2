import os
import pandas as pd
import re
from pandas.core.arraylike import default_array_ufunc
from pandas.core.nanops import F
from pandasql import sqldf
from componentes.utils.messages import messages
from configs import configs
import shutil
from decouple import config

m = None
if config('DEBUG', default=False):
    m = messages.Message()


def read_archive(path, mode='r'):
    try:
        with open(path, mode, encoding="utf-8") as arquivo:
            context = arquivo.read()
            if config('DEBUG', default=False):
                if context: # Verifica o conteúdo armazenado
                    txt = f"""
                    \n
                    Leitura do arquivo {path} concluida!
                    Contexto: {context}
                    """
                    m.safe(txt)
                else:
                    txt = f"""
                    \n
                    Leitura do arquivo {path} falha (arquivo vazio)
                    """
                    m.danger(txt)
            return context # Retorna o conteúdo
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        if config('DEBUG', default=False):
            m.danger(f"Erro ao ler arquivo: {e}")
        return "" # Retorna uma string vazia em caso de erro


def formater_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    columns = df.columns.tolist()
    mapped = {}
    for column in columns:
        new_column = column.upper()
        new_column = re.sub(r"[^A-Z0-9]", "_", new_column)
        new_column = re.sub(r"_+", "_", new_column).strip("_")
        mapped[column] = new_column
    return df.rename(columns=mapped)


def document_sql(query_sql: str, df: pd.DataFrame) -> str:
    if df is None:
        return "Erro: DataFrame não carregado. Não é possível executar consultas SQL."

    # 🔹 Garante que os nomes das colunas do DataFrame estejam em MAIÚSCULAS
    df = formater_dataframe(df)

    # 🔹 Converte a query da LLM para MAIÚSCULAS (compatível com colunas)
    query_sql_upper = query_sql.upper()

    try:
        # IMPORTANTE: no sqldf o alias deve bater com o nome usado na query
        result = sqldf(query_sql_upper, {'DF_INFO_DATASET': df})
    except Exception as e:
        return f"Erro ao executar query: {e}"

    if result is not None and not result.empty:
        return result.to_string(index=False)

    return "Consulta SQL retornou vazio."


def get_csv(file_path: str) -> pd.DataFrame | None:
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        if config('DEBUG', default=False):
            m.danger(f"Erro ao carregar arquivo: {file_path}\n{e}")

def load_text_archive(archive_name: str = "regras.txt", folder: str = 'docs') -> str:
    try:
        return os.path.join(folder, archive_name)
    except Exception as e:
        if config('DEBUG', default=False):
            m.danger("Erro ao carregar arquivo de texto: ", e)
        return ""


def delete_if_exists(path: str):
    """
    Verifica se um arquivo ou pasta existe no caminho especificado.
    Se existir, remove o arquivo ou diretório (recursivamente).
    """
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)
            print(f"Arquivo removido: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Pasta removida: {path}")
    else:
        print(f"Nada encontrado em: {path}")


def search_archive(dir_path: str) -> str:
    "Retorna um arquivo presente em um diretório especificado"
    if os.path.exists(dir_path):
        files = os.listdir(dir_path)
        m.any_color(f"Arquivos: {files}", 'orange') if m is not None else ""
        if files:
            return files[0]  # pega o primeiro arquivo

    return ""
