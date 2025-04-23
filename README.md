# Sync - YouTube to Spotify Playlist Sync

A web application that allows users to sync their YouTube playlists with Spotify, automatically identifying cover songs and finding the original tracks.

## Features

- User authentication with email and password
- Spotify OAuth integration
- YouTube playlist parsing
- OpenAI-powered cover song detection
- Spotify track matching
- Playlist creation and management

## Prerequisites

- Docker and Docker Compose
- Python 3.11
- Poetry
- API keys for:
  - YouTube Data API
  - Spotify Developer
  - OpenAI

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django settings
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database settings
POSTGRES_USER=rdb
POSTGRES_PASSWORD=your-password
POSTGRES_DB=vaughndv
DB_HOST=db
DB_PORT=5432

# API credentials
YOUTUBE_API_KEY=your-youtube-api-key
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/social-auth/complete/spotify/
OPENAI_API_KEY=your-openai-api-key
```

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sync.git
   cd sync
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Build and start the Docker containers:
   ```bash
   docker-compose up --build
   ```

4. Run database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Usage

1. Access the application at http://localhost:8000
2. Register a new account or log in
3. Connect your Spotify account
4. Enter a YouTube playlist URL
5. Review the proposed Spotify tracks
6. Confirm to create the Spotify playlist

## Development

To run the development server:

```bash
docker-compose up
```

The application will be available at http://localhost:8000

## Testing

To run tests:

```bash
docker-compose exec web python manage.py test
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 