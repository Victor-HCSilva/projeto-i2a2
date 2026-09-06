# =========================================
# Dockerfile final otimizado para seu projeto
# Local: ./.docker/Dockerfile
# =========================================

# 1️⃣ Imagem base com Python 3.12 slim
FROM python:3.12-slim-bullseye

# 2️⃣ Variável de trabalho
WORKDIR /app

# 3️⃣ Atualizar pacotes e instalar dependências do sistema
RUN apt update && apt upgrade -y && \
    apt install -y git curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# 4️⃣ Copiar requirements e arquivos principais
COPY requirements.txt /app/requirements.txt
COPY .docker/setup/setup.sh /app/setup.sh
COPY main.py /app/
COPY app.py /app/
COPY utils/ /app/utils/
COPY tools/ /app/tools/
COPY vectors/ /app/vectors/
COPY configs/ /app/configs/
COPY schemas/ /app/schemas/

# 5️⃣ Permissão de execução e execução do script de setup
RUN chmod +x /app/setup.sh && /app/setup.sh

# 6️⃣ Expor porta do Streamlit
EXPOSE 8501

# 7️⃣ Comando padrão ao iniciar container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
