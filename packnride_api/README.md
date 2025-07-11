# PacknRide API (Flask Backend)

This is a Flask-based backend API for the PacknRide application. It includes User Authentication, core Ride-Hailing features, and a Driving Monitoring Portal. This version uses in-memory data storage for simplicity.

## Project Structure

```
packnride_api/
├── app/                  # Main application package
│   ├── __init__.py       # Application factory, initializes Flask app & extensions
│   ├── auth.py           # Authentication routes (register, login)
│   ├── models.py         # Data models (currently conceptual for in-memory store)
│   ├── routes.py         # Main API routes for ride-hailing
│   ├── monitoring_routes.py # API routes for Driving Monitoring Portal
│   └── utils.py          # Utility functions (e.g., password hashing)
├── tests/                # Pytest tests
│   ├── conftest.py       # Pytest fixtures
│   ├── test_auth.py      # Tests for authentication
│   ├── test_rides.py     # Tests for ride-hailing
│   └── test_monitoring.py # Tests for monitoring portal
├── config.py             # Configuration classes (Dev, Prod, Test)
├── run.py                # Script to run the Flask development server
├── requirements.txt      # Python dependencies
└── .env.example          # Example environment variables
```

## Setup and Running

1.  **Clone the repository (if applicable) or ensure you have the files.**
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: If `pip install` fails due to `getcwd` errors in certain sandboxed environments, manual setup of dependencies might be needed, or testing in a different environment.)*
4.  **Set up environment variables:**
    *   Rename `.env.example` to `.env`.
    *   Fill in the required values in `.env`, especially `SECRET_KEY` and `JWT_SECRET_KEY`.
    ```env
    # .env
    SECRET_KEY=your_flask_secret_key_here
    JWT_SECRET_KEY=your_jwt_secret_key_here
    FLASK_ENV=development
    ```
5.  **Run the application:**
    ```bash
    python run.py
    ```
    The API should now be running on `http://0.0.0.0:5000`.

6.  **Running Tests (Recommended in a standard environment):**
    ```bash
    # Ensure dependencies including pytest and pytest-flask are installed
    # From the packnride_api directory:
    PYTHONPATH=. pytest tests/ -v
    ```
    *(Note: Test execution might fail in some sandboxed environments due to `getcwd` errors.)*


## API Endpoints

All main API routes are prefixed with `/api`, authentication routes with `/auth`, and monitoring routes with `/api/monitoring`.
A JWT access token is required for protected endpoints (indicated by `🔒`). Send the token in the `Authorization` header as `Bearer <token>`.
Admin access is typically required for monitoring endpoints and is controlled by an `is_admin` claim in the JWT.

---

### Health Check

*   **GET /health**
    *   Description: Checks if the API is running.
    *   Response: `200 OK` - `"PacknRide API is healthy!"`

---

### Authentication (`/auth`)

1.  **POST /auth/register**
    *   Description: Registers a new user.
    *   Request Body:
        ```json
        {
            "name": "Test User",
            "email": "user@example.com",
            "password": "password123",
            "user_type": "passenger", // or "driver"
            "is_admin": false // optional, defaults to false
        }
        ```
    *   Response: `201 Created` (user object including `is_admin` status)
    *   Error Responses: `400 Bad Request`, `409 Conflict`.

2.  **POST /auth/login**
    *   Description: Logs in an existing user.
    *   Request Body: (email, password)
    *   Response: `200 OK` (`{"access_token": "..."}`)
    *   Error Responses: `400 Bad Request`, `401 Unauthorized`, `404 Not Found`.

---

### Rides (`/api/rides`)

1.  **POST /api/rides/request** 🔒 (Passenger)
    *   Request: `{"pickup_location": "...", "dropoff_location": "..."}`
    *   Response: `201 Created` (ride object)

2.  **GET /api/rides/<ride_id>** 🔒 (Passenger or assigned Driver)
    *   Response: `200 OK` (ride object)

3.  **POST /api/rides/<ride_id>/accept** 🔒 (Driver)
    *   Response: `200 OK` (updated ride object)

4.  **PUT /api/rides/<ride_id>/status** 🔒 (Passenger or assigned Driver, rules apply)
    *   Request: `{"status": "new_status"}` (e.g., "en_route_pickup", "completed", "cancelled")
    *   Response: `200 OK` (updated ride object)

5.  **POST /api/rides/estimate_fare** 🔒 (Mocked)
    *   Request: `{"pickup_location": "...", "dropoff_location": "..."}`
    *   Response: `200 OK` (mocked fare estimation)

---

### Drivers (`/api/drivers`)

1.  **GET /api/drivers/nearby** 🔒 (Passenger, Mocked)
    *   Response: `200 OK` (list of available drivers)

---

### Driving Monitoring Portal (`/api/monitoring`)

1.  **POST /api/monitoring/events** 🔒 (Admin or Self-Driver)
    *   Description: Logs a new driving event (e.g., speeding, harsh braking).
    *   Request Body:
        ```json
        {
            "driver_id": 1,
            "ride_id": 101, // optional
            "event_type": "speeding",
            "timestamp": "2023-11-15T10:30:00Z",
            "location_lat": -25.7479,
            "location_lon": 28.2293,
            "details": {"speed_kmh": 120, "limit_kmh": 80}
        }
        ```
    *   Response: `201 Created` (event object)

2.  **GET /api/monitoring/drivers/<driver_id>/events** 🔒 (Admin or Self-Driver)
    *   Description: Retrieves driving events for a specific driver.
    *   Query Params: `event_type` (optional)
    *   Response: `200 OK` (`{"driver_id": X, "events": [...]}`)

3.  **GET /api/monitoring/drivers/<driver_id>/score** 🔒 (Admin or Self-Driver)
    *   Description: Retrieves the performance score for a driver.
    *   Response: `200 OK` (score object, or default if none exists)

4.  **PUT /api/monitoring/drivers/<driver_id>/score** 🔒 (Admin only)
    *   Description: Manually updates a driver's performance score.
    *   Request Body:
        ```json
        {
            "overall_safety_score": 85, // 0-100
            "efficiency_score": 90,   // 0-100
            "punctuality_score": 75,  // 0-100
            "feedback_summary": "Generally good, watch speed on Main St."
        }
        ```
    *   Response: `200 OK` (updated score object)

5.  **POST /api/monitoring/incidents** 🔒 (Admin only)
    *   Description: Logs a new incident report.
    *   Request Body:
        ```json
        {
            "driver_id": 1,
            "ride_id": 102, // optional
            "incident_type": "minor_accident",
            "description": "Minor collision, no injuries.",
            "status": "open" // 'open', 'investigating', 'resolved', 'closed'
        }
        ```
    *   Response: `201 Created` (incident report object)

6.  **GET /api/monitoring/incidents** 🔒 (Admin only)
    *   Description: Retrieves a list of all incidents.
    *   Query Params: `driver_id`, `status` (optional)
    *   Response: `200 OK` (`{"incidents": [...]}`)

7.  **GET /api/monitoring/incidents/<report_id>** 🔒 (Admin only)
    *   Description: Retrieves details of a specific incident.
    *   Response: `200 OK` (incident report object)

8.  **PUT /api/monitoring/incidents/<report_id>** 🔒 (Admin only)
    *   Description: Updates an incident report.
    *   Request Body:
        ```json
        {
            "status": "resolved",
            "resolution_notes": "Driver cautioned, passenger compensated."
        }
        ```
    *   Response: `200 OK` (updated incident report object)

---

## Future Considerations (Not Implemented)

*   Database integration (e.g., PostgreSQL, MongoDB).
*   Real-time GPS data ingestion for events.
*   Automated calculation of driver scores from events.
*   Advanced filtering and reporting for monitoring.
*   Push notifications for critical alerts.
*   More sophisticated Role-Based Access Control (RBAC).
*   Dedicated frontends for Admin Portal and User Apps.
*   Modules for Food Delivery, Courier Services.
```
