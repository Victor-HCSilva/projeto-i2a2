import pandas as pd
from utils.messages.utils.utils import get_csv, formater_dataframe

csv_path = './dataset/dataset.csv' # Ou o caminho real do seu CSV
df = get_csv(csv_path)
if df is not None:
    df_formatted = formater_dataframe(df)
    print("Colunas formatadas do DataFrame:")
    print(df_formatted.columns.tolist())
else:
    print("Erro: DataFrame não pôde ser carregado.")
