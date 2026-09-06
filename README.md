# 📊 Agente de Análise de CSV (Gemini + Streamlit)

> **⚠️ Atenção:** O aplicativo requer a variável `GEMINI_API_KEY` definida em `secrets.toml` ou nas variáveis de ambiente. Se ausente, será exibido um aviso amigável na interface.

## Visão geral
Este repositório contém uma aplicação **Streamlit** que permite análise interativa de arquivos CSV usando um agente LLM (**Gemini 1.5 Flash**) e ferramentas de visualização com Plotly.

## Estrutura do projeto
```
projeto-i2a2/
├─ app.py           # Código principal da aplicação Streamlit
├─ README.md       # Este documento
├─ requirements.txt # Dependências do projeto
└─ grafico.html    # Arquivo gerado temporariamente para visualização de gráficos
```

## Pré‑requisitos
- Python 3.10+ instalado
- Pip
- Uma chave de API válida para o modelo **Gemini** (definida em `.streamlit/secrets.toml` como `GEMINI_API_KEY`)

## Instalação
```bash
# Clone o repositório
git clone <url-do-repositorio>
cd projeto-i2a2

# Crie um ambiente virtual (opcional, mas recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

## Execução da aplicação
```bash
streamlit run app.py
```
A aplicação será aberta no navegador (geralmente em `http://localhost:8501`).

### Como usar
1. **Carregue um CSV** usando o uploader da página.
2. Visualize as primeiras linhas da tabela.
3. No campo de chat, faça perguntas ao agente, por exemplo:
   - "Quais são as colunas?"
   - "Descreva os dados"
   - "Crie um gráfico de barras para a coluna `data` e `vendas_ocorridas`"
4. Se o agente gerar um gráfico, ele será salvo em `grafico.html` e exibido na interface, com opção de download.

## Personalização
- Ajuste o caminho `GRAFICO_PATH` em `app.py` se desejar salvar os gráficos em outro diretório.
- Modifique os prompts do agente em `app.py` para adaptar o comportamento.

## Arquitetura do Projeto
O projeto está organizado da seguinte forma:

```
projeto-i2a2/
├─ app.py            # Aplicação Streamlit que orquestra o LLM Gemini e as ferramentas de visualização
├─ grafico.html      # Arquivo temporário onde os gráficos gerados são salvos
├─ requirements.txt  # Dependências Python (Streamlit, LangChain, Plotly, scikit-learn, etc.)
├─ .streamlit/       # Configuração de segredos do Streamlit (GEMINI_API_KEY)
└─ .gitignore        # Regras para ignorar arquivos locais e diretórios de cache
```

A camada de **LLM** (`langchain_google_genai.ChatGoogleGenerativeAI`) recebe a mensagem e, quando necessário, invoca as **ferramentas**:
- `descrever_dados`
- `identificar_padroes`
- `gerar_grafico`

Os gráficos são renderizados com **Plotly**, salvos em `grafico.html` e exibidos dinamicamente na interface Streamlit.

## Licença
Este projeto está licenciado sob a *MIT License* – sinta‑se livre para usar, modificar e distribuir.
