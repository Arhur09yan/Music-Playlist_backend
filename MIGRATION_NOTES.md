# Database Migration Notes

## Adding `local_file_path` Column to Songs Table

A new column `local_file_path` has been added to the `songs` table to store the path to locally cached audio files.

### Automatic Migration

SQLAlchemy's `Base.metadata.create_all()` will automatically add the new column when the application starts. However, for existing databases, you may need to:

1. **Option 1: Let SQLAlchemy handle it** (recommended for development)

   - The column will be added automatically on next app start
   - Existing songs will have `local_file_path = NULL`

2. **Option 2: Manual migration via Docker** (recommended)

   ```bash
   cd backend
   docker compose exec db psql -U music_user -d music_db -c "ALTER TABLE songs ADD COLUMN IF NOT EXISTS local_file_path VARCHAR;"
   ```

3. **Option 3: Manual SQL** (if connecting directly)
   ```sql
   ALTER TABLE songs ADD COLUMN IF NOT EXISTS local_file_path VARCHAR;
   ```

### Re-downloading Audio Files

After the migration, you may want to re-import songs to download their audio files:

```bash
# Using the Makefile
make import-spotify QUERY="rock music" LIMIT=20

# Or using the Python script
cd backend
docker compose exec api python scripts/import_spotify_songs.py "rock music" 10
```

New songs imported will automatically have their preview audio files downloaded and cached locally.

---

## Adding `albums` Table and `album_id` Foreign Key on Songs

A new `albums` table is introduced to store album metadata and relate songs to albums.

### Database Changes

1. **Create `albums` table**

   ```sql
   CREATE TABLE IF NOT EXISTS albums (
     id SERIAL PRIMARY KEY,
     title VARCHAR NOT NULL,
     artist VARCHAR NOT NULL,
     image_url VARCHAR,
     description VARCHAR,
     created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
   );
   ```

2. **Add `album_id` foreign key to `songs` table**

   ```sql
   ALTER TABLE songs
     ADD COLUMN IF NOT EXISTS album_id INTEGER,
     ADD CONSTRAINT songs_album_id_fkey
       FOREIGN KEY (album_id) REFERENCES albums(id)
       ON DELETE SET NULL;
   ```

### Applying via Docker

From the `backend` directory:

```bash
cd backend
docker compose exec db psql -U music_user -d music_db -c "
  CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    artist VARCHAR NOT NULL,
    image_url VARCHAR,
    description VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
  );
"

docker compose exec db psql -U music_user -d music_db -c "
  ALTER TABLE songs
    ADD COLUMN IF NOT EXISTS album_id INTEGER;
"

docker compose exec db psql -U music_user -d music_db -c "
  ALTER TABLE songs
    ADD CONSTRAINT IF NOT EXISTS songs_album_id_fkey
    FOREIGN KEY (album_id) REFERENCES albums(id)
    ON DELETE SET NULL;
"
```

After this migration, you can start creating albums and associating songs with them via the new API routes.
