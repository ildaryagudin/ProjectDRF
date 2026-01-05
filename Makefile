# Makefile
.PHONY: help build up down restart logs ps shell db-shell test migrate collectstatic create-superuser

help:
	@echo "Доступные команды:"
	@echo "  make build      - Сборка образов"
	@echo "  make up         - Запуск всех сервисов"
	@echo "  make down       - Остановка всех сервисов"
	@echo "  make restart    - Перезапуск сервисов"
	@echo "  make logs       - Просмотр логов"
	@echo "  make ps         - Статус контейнеров"
	@echo "  make shell      - Вход в контейнер backend"
	@echo "  make db-shell   - Вход в контейнер базы данных"
	@echo "  make test       - Запуск тестов"
	@echo "  make migrate    - Применение миграций"
	@echo "  make createsuperuser - Создание суперпользователя"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

ps:
	docker-compose ps

shell:
	docker-compose exec backend bash

db-shell:
	docker-compose exec postgres psql -U lms_user -d lms_db

test:
	docker-compose exec backend python manage.py test

migrate:
	docker-compose exec backend python manage.py migrate

createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

backup-db:
	docker-compose exec postgres pg_dump -U lms_user lms_db > backup_$(date +%Y%m%d_%H%M%S).sql

restore-db:
	@read -p "Имя файла для восстановления: " file && \
	docker-compose exec -T postgres psql -U lms_user -d lms_db < $$file

dev:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

clean:
	docker-compose down -v
	docker system prune -f