#!/bin/bash
# Simple script to add songs to database from Spotify

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎵 Adding Songs to Database from Spotify${NC}\n"

# Check if database is running
if ! docker compose ps db | grep -q "Up"; then
    echo "Starting database..."
    docker compose up db -d
    sleep 3
fi

# Default values
QUERY="${1:-popular music 2024}"
LIMIT="${2:-20}"

echo -e "${GREEN}Importing: '${QUERY}' (limit: ${LIMIT})${NC}\n"

docker compose run --rm \
    -v "$(pwd)/scripts:/app/scripts" \
    -v "$(pwd)/.env:/app/.env" \
    -e DATABASE_URL=postgresql+psycopg2://music_user:music_password@db:5432/music_db \
    api python scripts/quick_import.py "${QUERY}" ${LIMIT}

echo -e "\n${GREEN}✅ Done!${NC}"


