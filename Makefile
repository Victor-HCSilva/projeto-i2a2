RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
RESET="\e[0m"   # Reseta para a cor padrão

install:
	@echo "$(BLUE)Iniciando setup do ambiente$(RESET)"
	@chmod +x .docker/setup/setup.sh
	@.docker/setup/setup.sh
run:
	@echo ""
	@python -m streamlit run app.py

docker-build:
	@docker build -f .docker/Dockerfile -t projeto-i2a2:latest .

docker-run:
	@docker run --rm -p 8501:8501 --env-file .env projeto-i2a2:latest

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
