# Mini Twitter API

A **FastAPI-based backend** for a Twitter-like social media application.  
It implements user authentication, tweet CRUD operations, likes, follows, a paginated feed, user profiles, and tweet search.  
Built using **FastAPI**, **SQLAlchemy**, and **JWT**, with over **90% test coverage** using `pytest`.

## Features
- **User Management**: Register new users and login with JWT tokens.
- **Tweet Operations**: Create, read (paginated and sorted), update, and delete tweets.
- **Likes**: Like/unlike tweets and retrieve users who liked a tweet.
- **Follows**: Follow/unfollow users with duplicate prevention.
- **Feed**: Paginated feed of tweets from followed users.
- **User Profile**: Retrieve user details, including tweet count, follower count, and following count.
- **Tweet Search**: Search tweets by keyword with pagination and like counts.
- **Security**: JWT-based authentication with token expiration and password hashing (bcrypt).
- **Testing**: 16 passing unit tests covering all endpoints, with 91% code coverage.

## Tech Stack
- **Framework**: FastAPI (for building the RESTful API)
- **Database**: SQLAlchemy ORM with SQLite (easy local setup)
- **Authentication**: PyJWT for tokens, Passlib for password hashing
- **Testing**: Pytest, Requests (for API calls), Coverage.py (91% coverage)
- **Python Version**: 3.13.1 (compatible with Python 3.8+)

## Setup
1. **Clone the Repository**:

2. **Create a Virtual Environment (recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Database Configuration**:

- The app uses SQLite with `twitter.db` in the project root (created automatically on first run).
- For testing, it switches to `test.db` (handled in tests).

## API Endpoints

| Method   | Endpoint             | Description                |
| -------- | -------------------- | -------------------------- |
| `POST`   | `/register`          | Register new user          |
| `POST`   | `/login`             | Login and get JWT token    |
| `POST`   | `/tweets`            | Create tweet               |
| `GET`    | `/tweets`            | Get all tweets (paginated) |
| `GET`    | `/tweets/me`         | Get my tweets              |
| `PUT`    | `/tweets/{id}`       | Update tweet               |
| `DELETE` | `/tweets/{id}`       | Delete tweet               |
| `POST`   | `/like`              | Like tweet                 |
| `DELETE` | `/like/{tweet_id}`   | Unlike tweet               |
| `GET`    | `/tweets/{id}/likes` | Get who liked tweet        |
| `POST`   | `/follow`            | Follow user                |
| `DELETE` | `/follow/{user_id}`  | Unfollow user              |
| `GET`    | `/feed`              | Get followed users’ tweets |
| `GET`    | `/users/{user_id}`   | Get user profile           |
| `GET`    | `/tweets/search`     | Search tweets              |


## Running the App

Start the Server with:

```bash
uvicorn app.main:app --reload
```

- The API will be available at `http://127.0.0.1:8000`.
- For Interactive API Docs, visit `http://127.0.0.1:8000/docs` (Swagger UI).

## Testing

In a different Terminal, run:
    
    pytest tests/test_api.py -v

View coverage report:

    pytest --cov=app --cov-report=term-missing

OR, test manually with the help of Swagger UI.

## Project Structure

```bash
mini_twitter/
├── app/
│   ├── __init__.py
│   ├── auth.py          # JWT authentication and password hashing
│   ├── database.py      # SQLAlchemy setup with SQLite
│   ├── main.py          # FastAPI app and all endpoints
│   ├── models.py        # SQLAlchemy models (User, Tweet, Like, Follow)
│   ├── schemas.py       # Pydantic models for requests/responses
├── tests/
│   ├── test_api.py      # Unit tests for all endpoints
├── .coveragerc          # Coverage configuration
├── .gitignore           # Ignores databases, caches, etc.
├── README.md            # This file
├── requirements.txt     # Dependencies
├── run_server.py        # Script to run server with coverage
└── twitter.db           # Development database (auto-created)
```

## Notes

- **Security**: Uses a hardcoded SECRET_KEY for development.
- **Database**: SQLite for simplicity.
- **Version 2 Plans**: Integrate AI/ML for tweet toxicity detection using Hugging Face models and Recommend Tweets Based on interests.
- **Coverage**: 91% achieved with pytest-cov. Missing branches are error handling paths (to be tested in future updates).
- **Contributions**: Feel free to fork and submit pull requests!

## License
MIT License. See LICENSE for details.

---
Built with ❤️ for learning backend development with FastAPI.
