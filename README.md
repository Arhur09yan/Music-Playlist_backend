# Music Streaming API - FastAPI Backend

A complete RESTful music streaming backend built with FastAPI, SQLAlchemy, and JWT authentication.

## Features

- JWT-based authentication (access & refresh tokens)
- User registration and login
- Full CRUD operations for songs
- Playlist management (create, view, add/remove songs)
- Like/unlike functionality with user-specific likes
- Full-text search across songs, artists, albums, and genres
- CORS support for frontend integration

## Project Structure

\`\`\`
backend/
├── app/
│ ├── main.py # FastAPI entry point
│ ├── config.py # Configuration & settings
│ ├── database.py # Database connection & session
│ ├── models/ # SQLAlchemy models
│ │ ├── user.py
│ │ ├── song.py
│ │ └── playlist.py
│ ├── schemas/ # Pydantic request/response schemas
│ │ ├── user.py
│ │ ├── song.py
│ │ └── playlist.py
│ ├── services/ # Business logic
│ │ ├── auth_service.py
│ │ └── playlist_service.py (includes LikeService)
│ ├── routes/ # API endpoints
│ │ ├── auth.py
│ │ ├── songs.py
│ │ ├── playlists.py
│ │ └── likes.py
│ └── utils/
│ └── security.py # Password hashing & JWT
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
\`\`\`

## Installation

### Local Setup

1. Clone the repository and navigate to backend folder:
   \`\`\`bash
   cd backend
   \`\`\`

2. Create a virtual environment:
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate
   \`\`\`

3. Install dependencies:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. Create `.env` file (copy from `.env.example`):
   \`\`\`bash
   cp .env.example .env
   \`\`\`

5. Run the server:
   \`\`\`bash
   uvicorn app.main:app --reload
   \`\`\`

The API will be available at `http://localhost:8000`

### Docker Setup

1. Build and run with Docker Compose:
   \`\`\`bash
   docker-compose up --build
   \`\`\`

2. Access the API at `http://localhost:8000`

## API Documentation

### Interactive Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Authentication Endpoints

**Register**
\`\`\`
POST /api/v1/auth/register
{
"email": "user@example.com",
"username": "username",
"password": "password123"
}
\`\`\`

**Login**
\`\`\`
POST /api/v1/auth/login
{
"email": "user@example.com",
"password": "password123"
}
Response: { "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
\`\`\`

**Get Current User**
\`\`\`
GET /api/v1/auth/me
Headers: Authorization: Bearer <access_token>
\`\`\`

**Refresh Token**
\`\`\`
POST /api/v1/auth/refresh
Headers: Authorization: Bearer <refresh_token>
\`\`\`

### Songs Endpoints

**Get All Songs**
\`\`\`
GET /api/v1/songs?skip=0&limit=20
\`\`\`

**Get Song Details**
\`\`\`
GET /api/v1/songs/{song_id}
\`\`\`

**Create Song** (Protected)
\`\`\`
POST /api/v1/songs
Headers: Authorization: Bearer <access_token>
{
"title": "Song Name",
"artist": "Artist Name",
"album": "Album Name",
"genre": "Genre",
"duration": 240.5,
"url": "https://..."
}
\`\`\`

**Update Song** (Protected)
\`\`\`
PUT /api/v1/songs/{song_id}
Headers: Authorization: Bearer <access_token>
\`\`\`

**Delete Song** (Protected)
\`\`\`
DELETE /api/v1/songs/{song_id}
Headers: Authorization: Bearer <access_token>
\`\`\`

**Search Songs**
\`\`\`
GET /api/v1/songs/search/query?q=search_term&skip=0&limit=20
\`\`\`

### Playlists Endpoints

**Create Playlist** (Protected)
\`\`\`
POST /api/v1/playlists
Headers: Authorization: Bearer <access_token>
{
"name": "My Playlist",
"description": "Description here"
}
\`\`\`

**Get User Playlists** (Protected)
\`\`\`
GET /api/v1/playlists
Headers: Authorization: Bearer <access_token>
\`\`\`

**Get Playlist Details**
\`\`\`
GET /api/v1/playlists/{playlist_id}
\`\`\`

**Add Song to Playlist** (Protected)
\`\`\`
POST /api/v1/playlists/{playlist_id}/songs/{song_id}
Headers: Authorization: Bearer <access_token>
\`\`\`

**Remove Song from Playlist** (Protected)
\`\`\`
DELETE /api/v1/playlists/{playlist_id}/songs/{song_id}
Headers: Authorization: Bearer <access_token>
\`\`\`

### Likes Endpoints

**Like Song** (Protected)
\`\`\`
POST /api/v1/likes/{song_id}
Headers: Authorization: Bearer <access_token>
\`\`\`

**Unlike Song** (Protected)
\`\`\`
DELETE /api/v1/likes/{song_id}
Headers: Authorization: Bearer <access_token>
\`\`\`

**Get User Likes** (Protected)
\`\`\`
GET /api/v1/likes?skip=0&limit=20
Headers: Authorization: Bearer <access_token>
\`\`\`

## Database Schema

### Users Table

- id (Primary Key)
- email (Unique)
- username (Unique)
- hashed_password
- created_at
- updated_at

### Songs Table

- id (Primary Key)
- title
- artist
- album
- genre
- duration
- url
- created_at

### Playlists Table

- id (Primary Key)
- name
- description
- owner_id (Foreign Key → Users)
- created_at
- updated_at

### PlaylistSongs Table (Join Table)

- id (Primary Key)
- playlist_id (Foreign Key → Playlists)
- song_id (Foreign Key → Songs)
- added_at

### Likes Table

- id (Primary Key)
- user_id (Foreign Key → Users)
- song_id (Foreign Key → Songs)
- created_at

## Environment Variables

\`\`\`env
DATABASE_URL=sqlite:///./music.db # SQLite (dev), or PostgreSQL URL
SECRET_KEY=your-secret-key-here # Change for production
ALGORITHM=HS256 # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=30 # Token expiration time
REFRESH_TOKEN_EXPIRE_DAYS=7 # Refresh token expiration
DEBUG=True # Debug mode (set to False in production)
\`\`\`

## Security Considerations

1. Change `SECRET_KEY` in production to a strong random string
2. Use HTTPS in production
3. Restrict `allow_origins` in CORS middleware to specific frontend domains
4. Use environment variables for sensitive data
5. Consider adding rate limiting
6. Implement token blacklisting for logout functionality
7. Add input validation and sanitization

## Production Deployment

For production, consider:

- Using PostgreSQL instead of SQLite
- Setting up a proper secret key management system
- Implementing API rate limiting
- Adding request logging and monitoring
- Setting up automated backups
- Using a production WSGI server like Gunicorn
- Implementing pagination limits and caching

## License

MIT
