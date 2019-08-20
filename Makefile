.PHONY: sass sass-watch dev-env docker docker-clean docker-init docker-makemigrations docker-migrate docker-makemessages docker-compilemessages docker-pw

.DEFAULT_GOAL := help

DJANGO_ADMIN_USER=admin
PGPASSWORD=kairos
DB_PORT=5432

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort -k 1,1 | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

sass: ## Compile SASS to CSS
	@gulp sass

sass-watch: ## Compile SASS to CSS on every change
	@gulp sass:watch

dev-env: ## Install the development requirements
	@npm i

docker: ## Start the docker environment
	@docker-compose up --no-recreate

docker-clean: ## Remove the docker environment
	@docker-compose kill
	@docker-compose rm -f

docker-init: ## Initialize the docker environment
	@docker-compose up -d --no-recreate
	@docker exec -it kairos_web_1 python app/manage.py migrate
	@docker exec -it kairos_web_1 app/manage.py loaddata tools/docker/user.json
	@docker-compose stop

docker-makemigrations: ## Generate django migrations in the docker environment
	@docker exec -it kairos_web_1 python app/manage.py makemigrations

docker-migrate: ## Run django migrations in the docker environment
	@docker exec -it kairos_web_1 python app/manage.py migrate

docker-makemessages: ## Generate django translations in the docker environment
	@docker exec -it kairos_web_1 python app/manage.py makemessages -a

docker-compilemessages: ## Compile docker translations in the docker environment
	@docker exec -it kairos_web_1 python app/manage.py compilemessages

docker-pw: ## Change the django superuser password in the docker environment
	@docker exec -it kairos_web_1 python app/manage.py changepassword ${DJANGO_ADMIN_USER}
