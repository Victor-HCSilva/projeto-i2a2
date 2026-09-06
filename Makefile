RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
RESET="\e[0m"   # Reseta para a cor padrão

install:
	@echo "$(BLUE)Iniciando setup do ambiente"
	@echo ""
	@echo "Instalando dependencias"
	@echo ""
	@cd setup/
	@chmod +x setup.sh
	# Setup inciando ambiente python e intalando dependencias
	# Python, e Ollhama
	@./setup.sh
run:
	@echo ""
	@streamlit run app.py

save:
	@git add . ; git commit
	echo "$(GREEN) Arquivos adicionados ao git..."
	echo "$(BLUE) Não esqueça de fazer push"

push:
	#@nvim ~/configs/README.md
	echo "$(GREEN) Salvando arquivos no repositorio remoto..."
	echo ""
	git push origin develop || true

amend:
	@git add ~/configs
	@git commit --amend

force:
	@git push origin develop --force
