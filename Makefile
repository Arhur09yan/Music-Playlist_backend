.PHONY: help db-up db-down migrate migrate-liked migrate-playlist-songs migrate-all import-songs import-popular import-rock import-jazz import-hiphop

help:
	@echo "Available commands:"
	@echo "  make db-up              - Start PostgreSQL database"
	@echo "  make db-down            - Stop PostgreSQL database"
	@echo "  make migrate            - Create all tables from SQLAlchemy models (create_all)"
	@echo "  make migrate-liked      - Add 'liked' column to songs table (if missing)"
	@echo "  make migrate-playlist-songs - Create playlist_songs table if missing"
	@echo "  make migrate-all        - Run all migration helpers (migrate, liked, playlist_songs)"
	@echo "  make import-songs QUERY='rock music' LIMIT=20  - Import songs from Spotify"
	@echo "  make import-popular     - Import 30 popular songs"
	@echo "  make import-rock        - Import 25 rock songs"
	@echo "  make import-jazz        - Import 20 jazz songs"
	@echo "  make import-hiphop     - Import 20 hip hop songs"

db-up:
	docker compose up db -d

db-down:
	docker compose down

migrate:
	@echo "Running SQLAlchemy Base.metadata.create_all (create all tables)..."
	@docker compose run --rm \
		-v "$(PWD)/scripts:/app/scripts" \
		-v "$(PWD)/app:/app/app" \
		-v "$(PWD)/.env:/app/.env" \
		-e DATABASE_URL=postgresql+psycopg2://music_user:music_password@db:5432/music_db \
		api python scripts/migrate_all.py

migrate-liked:
	@echo "Adding 'liked' column to songs table if it does not exist..."
	@docker compose run --rm \
		-v "$(PWD)/scripts:/app/scripts" \
		-v "$(PWD)/app:/app/app" \
		-v "$(PWD)/.env:/app/.env" \
		-e DATABASE_URL=postgresql+psycopg2://music_user:music_password@db:5432/music_db \
		api python scripts/add_liked_column.py

migrate-playlist-songs:
	@echo "Creating playlist_songs table if it does not exist..."
	@docker compose run --rm \
		-v "$(PWD)/scripts:/app/scripts" \
		-v "$(PWD)/app:/app/app" \
		-v "$(PWD)/.env:/app/.env" \
		-e DATABASE_URL=postgresql+psycopg2://music_user:music_password@db:5432/music_db \
		api python scripts/add_playlist_songs_table.py

migrate-all:
	@echo "Running full migration helpers (create_all, liked column, playlist_songs table)..."
	@$(MAKE) migrate
	@$(MAKE) migrate-liked
	@$(MAKE) migrate-playlist-songs

import-songs:
	@if [ -z "$(QUERY)" ]; then \
		echo "Error: QUERY is required. Example: make import-songs QUERY='rock music' LIMIT=20"; \
		exit 1; \
	fi
	@LIMIT=$${LIMIT:-20}; \
	docker compose run --rm \
		-v "$(PWD)/scripts:/app/scripts" \
		-v "$(PWD)/.env:/app/.env" \
		-e DATABASE_URL=postgresql+psycopg2://music_user:music_password@db:5432/music_db \
		api python scripts/quick_import.py "$(QUERY)" $$LIMIT

import-popular:
	@echo "Importing popular music..."
	@make import-songs QUERY="popular music 2024" LIMIT=30

import-rock:
	@echo "Importing rock music..."
	@make import-songs QUERY="rock classics" LIMIT=25

import-jazz:
	@echo "Importing jazz music..."
	@make import-songs QUERY="jazz music" LIMIT=20

import-hiphop:
	@echo "Importing hip hop music..."
	@make import-songs QUERY="hip hop" LIMIT=20

import-all:
	@echo "Importing all genres..."
	@make import-popular
	@make import-rock
	@make import-jazz
	@make import-hiphop


