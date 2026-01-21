# Workout Tracking API

A production-ready REST API backend for tracking workout sessions and providing personalized workout recommendations based on user performance. Built with FastAPI and SQLAlchemy.

## Features

- 🏋️ **Workout Session Management**: Start, log, and end workout sessions
- 📊 **Smart Recommendations**: Adaptive workout planning based on past performance
- 👥 **Multi-User Support**: Track workouts for multiple users
- 📈 **Progress Tracking**: View workout history and progression trends
- 🔄 **RESTful API**: Clean, versioned API with pagination and filtering
- ✅ **Input Validation**: Comprehensive request validation with detailed error messages
- 🔍 **Request Tracking**: UUID-based request IDs for debugging
- 📖 **Auto Documentation**: Interactive API docs with Swagger UI

## How It Works

### Workout Adaptation Algorithm

The system uses a simple yet effective algorithm to recommend your next workout:

- **Completed all reps** → Next workout: current reps + 2
- **Did not complete all reps** → Next workout: current reps - 1
- **Minimum reps**: Always at least 1

This progressive overload approach helps you continuously improve while adjusting to your current fitness level.

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd workout-api
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will start at `http://localhost:8000`

### Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users` | Create a new user |
| GET | `/api/v1/users/{user_id}` | Get user details with statistics |
| GET | `/api/v1/users` | List all users (paginated) |

### Workouts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users/{user_id}/workouts` | Start a new workout session |
| GET | `/api/v1/users/{user_id}/workouts` | Get user's workout history |
| GET | `/api/v1/workouts/{session_id}` | Get specific workout details |
| PATCH | `/api/v1/workouts/{session_id}/log` | Log exercise results |
| PATCH | `/api/v1/workouts/{session_id}/end` | End workout and get recommendation |

### Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/{user_id}/recommendations` | Get next workout recommendation |

## Usage Examples

### 1. Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2026-01-21T14:28:00Z",
    "total_workouts": 0
  },
  "meta": {
    "timestamp": "2026-01-21T14:28:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 2. Start a Workout

```bash
curl -X POST "http://localhost:8000/api/v1/users/1/workouts" \
  -H "Content-Type: application/json" \
  -d '{"assigned_reps": 10, "exercise_name": "Push-ups"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 1,
    "started_at": "2026-01-21T14:30:00Z",
    "ended_at": null,
    "status": "active",
    "exercise": {
      "assigned_reps": 10,
      "completed_reps": null,
      "exercise_name": "Push-ups",
      "completion_percentage": null
    }
  },
  "links": {
    "log": "/api/v1/workouts/1/log",
    "end": "/api/v1/workouts/1/end"
  }
}
```

### 3. Log Exercise Results

```bash
curl -X PATCH "http://localhost:8000/api/v1/workouts/1/log" \
  -H "Content-Type: application/json" \
  -d '{"completed_reps": 10}'
```

### 4. End Workout

```bash
curl -X PATCH "http://localhost:8000/api/v1/workouts/1/end"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": 1,
    "ended_at": "2026-01-21T14:32:00Z",
    "duration_minutes": 2.0,
    "summary": {
      "assigned_reps": 10,
      "completed_reps": 10,
      "performance": "completed",
      "next_recommended_reps": 12
    }
  },
  "message": "Workout completed! Next workout: 12 reps"
}
```

### 5. Get Recommendation

```bash
curl "http://localhost:8000/api/v1/users/1/recommendations"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "recommended_reps": 12,
    "recommendation_reason": "Completed all reps in last session",
    "last_workout": {
      "session_id": 1,
      "assigned_reps": 10,
      "completed_reps": 10,
      "date": "2026-01-21T14:32:00Z"
    },
    "progression": {
      "trend": "improving",
      "total_increase": 2,
      "sessions_count": 1
    }
  }
}
```

## Design Decisions

### Architecture Choices

**API Versioning** (`/api/v1`)
- Allows future API versions without breaking existing clients
- Enables gradual migration and backwards compatibility

**Response Envelope Pattern**
- Consistent response structure across all endpoints
- Makes client-side error handling predictable
- Includes metadata (timestamp, request ID) for debugging

**RESTful Design**
- Proper HTTP methods: POST (create), GET (read), PATCH (update)
- Meaningful status codes: 201 (created), 404 (not found), 409 (conflict), 422 (validation error)
- Resource-based URLs showing clear hierarchies: `/users/{user_id}/workouts`

**HATEOAS Links**
- Responses include navigation links for discoverability
- Clients can follow links without hardcoding URLs

**Pagination**
- Prevents overwhelming responses
- Improves performance for large datasets
- Configurable page size with maximum limit

### Database Design

**SQLite**
- Zero configuration required
- Perfect for development and demos
- Single-file database for portability
- Easily swappable for PostgreSQL/MySQL in production

**Denormalized WorkoutRecommendation Table**
- Optimized for O(1) lookup of next recommendation
- Avoids complex calculations on every request
- Updated transactionally when workouts are completed

**Relationships & Cascades**
- Proper foreign keys with cascade deletes
- Ensures data integrity
- Prevents orphaned records

### Validation Strategy

**Multi-Layer Validation**
- Pydantic schemas validate request format and types
- Business logic validates domain rules (e.g., no duplicate active sessions)
- Database constraints ensure data integrity

**Detailed Error Messages**
- Structured error responses with error codes
- Field-level error information
- Helps clients handle errors gracefully

### Technology Choices

**FastAPI**
- High performance with async support
- Automatic API documentation
- Built-in request validation with Pydantic
- Modern Python type hints

**SQLAlchemy**
- Mature and battle-tested ORM
- Flexible and powerful query API
- Good abstraction over raw SQL
- Easy to switch databases

**Pydantic**
- Data validation using Python type annotations
- Automatic JSON serialization/deserialization
- Clear error messages for invalid data

## Project Structure

```
workout-api/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI app & startup
│   ├── database.py           # Database configuration
│   ├── models.py             # SQLAlchemy models
│   ├── schemas.py            # Pydantic schemas
│   ├── crud.py               # Database operations
│   ├── exceptions.py         # Custom exceptions
│   ├── middleware.py         # Request tracking & error handling
│   └── routers/
│       ├── __init__.py
│       ├── users.py          # User endpoints
│       ├── workouts.py       # Workout endpoints
│       └── recommendations.py # Recommendation endpoints
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
└── workout.db               # SQLite database (auto-created)
```

## Testing the API

You can test the API using:

1. **Interactive Docs** (Recommended for beginners)
   - Visit http://localhost:8000/docs
   - Click "Try it out" on any endpoint
   - Fill in parameters and click "Execute"

2. **curl** (Command line)
   - See examples above

3. **Postman/Insomnia** (GUI clients)
   - Import the OpenAPI spec from http://localhost:8000/openapi.json

4. **Python requests**
   ```python
   import requests
   
   # Create a user
   response = requests.post(
       "http://localhost:8000/api/v1/users",
       json={"name": "Jane Doe"}
   )
   print(response.json())
   ```

## Error Handling

The API uses HTTP status codes and structured error responses:

```json
{
  "success": false,
  "data": null,
  "errors": [
    {
      "code": "USER_NOT_FOUND",
      "message": "User with ID 999 does not exist",
      "field": "user_id"
    }
  ],
  "meta": {
    "timestamp": "2026-01-21T14:28:00Z",
    "request_id": "uuid"
  }
}
```

### Common Error Codes

- `USER_NOT_FOUND`: User doesn't exist (404)
- `WORKOUT_SESSION_NOT_FOUND`: Session doesn't exist (404)
- `ACTIVE_SESSION_EXISTS`: User already has an active workout (409)
- `SESSION_NOT_ACTIVE`: Cannot log/end inactive session (409)
- `EXERCISE_NOT_LOGGED`: Cannot end session without logging reps (409)
- `VALIDATION_ERROR`: Invalid request data (422)

## Future Enhancements

Potential improvements for production deployment:

- [ ] User authentication (JWT tokens)
- [ ] Multiple exercises per workout session
- [ ] Exercise types and categories
- [ ] Workout templates and programs
- [ ] Analytics and reporting endpoints
- [ ] Export workout data (CSV, JSON)
- [ ] Rate limiting and throttling
- [ ] Caching layer (Redis)
- [ ] Database migrations (Alembic)
- [ ] Unit and integration tests
- [ ] Docker containerization
- [ ] CI/CD pipeline

## License

This project is created for demonstration purposes.

## Author

Built as a backend assessment project demonstrating:
- Clean API design and architecture
- Database modeling and ORM usage  
- Input validation and error handling
- RESTful best practices
- Code organization and documentation
