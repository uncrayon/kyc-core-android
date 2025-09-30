.PHONY: run reload-config seed-red-team

run:
	@docker info >/dev/null 2>&1 || ( \
		echo "Docker daemon is not running. Please start Docker before running 'make run'." && exit 1 \
	)
	docker-compose up -d

reload-config:
	docker-compose restart

seed-red-team:
	@echo "Seeding red team data..."
	docker-compose exec api python scripts/seed_red_team.py
