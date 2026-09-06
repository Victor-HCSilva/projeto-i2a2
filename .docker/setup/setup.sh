#!/bin/bash

echo "🚀 Iniciando instalação do agente de IA..."

# 1. Atualizar pacotes
apt update && apt upgrade -y

# 2. Instalar dependências básicas
apt install -y python3 python3-venv python3-pip git curl

# 3. Atualizar pip
pip install --upgrade pip

# 4. Instalar bibliotecas do projeto
pip install -r /app/requirements.txt

# 5. Instalar Ollama (se não existir)
if ! command -v ollama &> /dev/null
then
    echo "📥 Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama já está instalado."
fi

# 6. Baixar modelos (não interativo ideal)
echo "📥 Baixando modelos necessários..."
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
ollama pull qwen3

echo ""
echo "🎉 Instalação concluída!"
