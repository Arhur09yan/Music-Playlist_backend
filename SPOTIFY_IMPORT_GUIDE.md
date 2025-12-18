# How to Import Music from Spotify to Database

## Step 1: Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create an app"**
4. Fill in:
   - **App name**: (e.g., "Music Streaming App")
   - **App description**: (e.g., "Music streaming backend")
   - **Redirect URI**: (leave empty or use `http://localhost:8000/callback`)
   - Check the terms and click **"Save"**
5. Copy your **Client ID** and **Client Secret**

## Step 2: Create .env File

Create a `.env` file in the project root (`/Users/artur/Desktop/backend-playlist/.env`) with:

```env
# Database Configuration (for local development)
DATABASE_URL=postgresql+psycopg2://music_user:music_password@localhost:5433/music_db

# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Server Configuration
DEBUG=True
API_V1_STR=/api/v1
ALLOWED_ORIGINS=*

# Audio Storage
AUDIO_STORAGE_DIR=audio_storage
```

**Important**: Replace `your_spotify_client_id_here` and `your_spotify_client_secret_here` with your actual credentials from Step 1.

## Step 3: Start the Database

Make sure PostgreSQL is running in Docker:

```bash
cd /Users/artur/Desktop/backend-playlist
docker compose up db -d
```

## Step 4: Activate Virtual Environment

```bash
cd /Users/artur/Desktop/backend-playlist
source .venv/bin/activate
```

## Step 5: Import Songs from Spotify

Run the import script with your search query:

```bash
# Import 20 songs matching "rock music"
python scripts/import_spotify_songs.py "rock music" 20

# Import 30 jazz songs
python scripts/import_spotify_songs.py "jazz classics" 30

# Import 50 pop hits
python scripts/import_spotify_songs.py "pop hits 2024" 50

# Import specific artist
python scripts/import_spotify_songs.py "artist:The Beatles" 20

# Import specific album
python scripts/import_spotify_songs.py "album:Abbey Road" 10
```

### Search Query Examples

- `"rock music"` - General rock music
- `"jazz classics"` - Jazz songs
- `"pop hits 2024"` - Recent pop hits
- `"artist:The Beatles"` - Songs by The Beatles
- `"album:Abbey Road"` - Songs from Abbey Road album
- `"genre:electronic"` - Electronic music
- `"year:2023"` - Songs from 2023

## What Gets Imported?

For each song, the script imports:
- **Title** - Song name
- **Artist** - Artist name
- **Album** - Album name
- **Genre** - Music genre
- **Duration** - Song duration (30s preview if available, or full duration)
- **URL** - Spotify preview URL (30-second preview) or Spotify track URL
- **Image URL** - Album cover image
- **Local File Path** - Downloaded preview audio file (if preview available)

## Troubleshooting

### Error: "Spotify client credentials are not configured"
- Make sure your `.env` file exists and has `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` set
- Restart your terminal/IDE to reload environment variables

### Error: "Failed to connect to Spotify API"
- Check your internet connection
- Verify your Spotify credentials are correct
- Make sure your Spotify app is active in the dashboard

### Error: "Database connection failed"
- Make sure PostgreSQL is running: `docker compose up db -d`
- Check that `DATABASE_URL` in `.env` points to `localhost:5433` (not `db:5432`)

### No songs found
- Try a different search query
- Some queries may not return results - try more general terms

## Viewing Imported Songs

After importing, you can:
1. Check the database directly
2. Use the API: `GET http://localhost:8000/api/v1/songs`
3. View in Swagger UI: `http://localhost:8000/docs`

