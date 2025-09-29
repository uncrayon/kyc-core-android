.PHONY: run reload-config seed-red-team

run:
	docker-compose up -d

reload-config:
	docker-compose restart

seed-red-team:
	@echo "Seeding red team data..."
	docker-compose exec api python scripts/seed_red_team.py