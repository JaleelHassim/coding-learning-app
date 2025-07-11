# PacknRide API (Flask Backend - Phase 1)

This is a simple Flask-based backend API for the PacknRide application, focusing on User Authentication and core Ride-Hailing features. This version uses in-memory data storage for simplicity.

## Project Structure

```
packnride_api/
├── app/                  # Main application package
│   ├── __init__.py       # Application factory, initializes Flask app & extensions
│   ├── auth.py           # Authentication routes (register, login)
│   ├── models.py         # Data models (currently conceptual for in-memory store)
│   ├── routes.py         # Main API routes (rides, drivers)
│   └── utils.py          # Utility functions (e.g., password hashing)
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
    The API should now be running on `http://0.0.0.0:5000`. You will see output like:
    `Starting PacknRide API on 0.0.0.0:5000 with config: development`

## API Endpoints

All main API routes are prefixed with `/api`, and authentication routes with `/auth`.
A JWT access token is required for protected endpoints (indicated by `🔒`). Send the token in the `Authorization` header as `Bearer <token>`.

---

### Health Check

*   **GET /health**
    *   Description: Checks if the API is running.
    *   Response: `200 OK`
        ```json
        "PacknRide API is healthy!"
        ```

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
            "user_type": "passenger" // or "driver"
        }
        ```
    *   Response: `201 Created`
        ```json
        {
            "message": "User registered successfully",
            "user": {
                "id": 1,
                "name": "Test User",
                "email": "user@example.com",
                "user_type": "passenger"
            }
        }
        ```
    *   Error Responses: `400 Bad Request` (missing fields, invalid user_type), `409 Conflict` (email exists).

2.  **POST /auth/login**
    *   Description: Logs in an existing user.
    *   Request Body:
        ```json
        {
            "email": "user@example.com",
            "password": "password123"
        }
        ```
    *   Response: `200 OK`
        ```json
        {
            "access_token": "your_jwt_access_token_here"
        }
        ```
    *   Error Responses: `400 Bad Request` (missing fields), `401 Unauthorized` (invalid credentials), `404 Not Found` (email not found).

---

### Rides (`/api/rides`)

1.  **POST /api/rides/request** 🔒
    *   Description: Allows an authenticated 'passenger' to request a new ride.
    *   Request Body:
        ```json
        {
            "pickup_location": "123 Main St",
            "dropoff_location": "789 Oak Ave"
        }
        ```
    *   Response: `201 Created` (example)
        ```json
        {
            "message": "Ride requested successfully",
            "ride": {
                "id": 1,
                "passenger_id": 1,
                "driver_id": null,
                "pickup_location": "123 Main St",
                "dropoff_location": "789 Oak Ave",
                "status": "pending",
                "fare": null,
                "requested_at": "2023-10-27T10:00:00Z",
                "updated_at": "2023-10-27T10:00:00Z"
            }
        }
        ```
    *   Error Responses: `400 Bad Request`, `401 Unauthorized`, `403 Forbidden` (if not a passenger).

2.  **GET /api/rides/<ride_id>** 🔒
    *   Description: Retrieves details for a specific ride. Accessible by the passenger who requested or the assigned driver.
    *   Response: `200 OK` (example)
        ```json
        {
            "id": 1,
            "passenger_id": 1,
            "driver_id": 2,
            "pickup_location": "123 Main St",
            "dropoff_location": "789 Oak Ave",
            "status": "accepted",
            "fare": null,
            "requested_at": "2023-10-27T10:00:00Z",
            "updated_at": "2023-10-27T10:05:00Z"
        }
        ```
    *   Error Responses: `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

3.  **POST /api/rides/<ride_id>/accept** 🔒
    *   Description: Allows an authenticated 'driver' to accept a pending ride.
    *   Response: `200 OK` (example)
        ```json
        {
            "message": "Ride accepted successfully",
            "ride": {
                "id": 1,
                "passenger_id": 1,
                "driver_id": 2, // Driver's ID
                "pickup_location": "123 Main St",
                "dropoff_location": "789 Oak Ave",
                "status": "accepted",
                "fare": null,
                // ... timestamps
            }
        }
        ```
    *   Error Responses: `400 Bad Request` (ride not pending), `401 Unauthorized`, `403 Forbidden` (if not a driver), `404 Not Found`, `409 Conflict` (already accepted).

4.  **PUT /api/rides/<ride_id>/status** 🔒
    *   Description: Allows the authenticated passenger or driver to update the ride status.
    *   Valid statuses: `en_route_pickup`, `arrived_pickup`, `started`, `completed`, `cancelled`.
    *   Request Body:
        ```json
        {
            "status": "en_route_pickup"
        }
        ```
    *   Response: `200 OK` (example)
        ```json
        {
            "message": "Ride status updated to en_route_pickup",
            "ride": {
                // ... updated ride object
                "status": "en_route_pickup"
            }
        }
        ```
    *   Error Responses: `400 Bad Request` (invalid status), `401 Unauthorized`, `403 Forbidden` (invalid transition or not authorized), `404 Not Found`.

5.  **POST /api/rides/estimate_fare** 🔒
    *   Description: (Mocked) Provides a mock fare estimation.
    *   Request Body:
        ```json
        {
            "pickup_location": "Point A",
            "dropoff_location": "Point B"
        }
        ```
    *   Response: `200 OK` (example)
        ```json
        {
            "pickup_location": "Point A",
            "dropoff_location": "Point B",
            "estimated_fare_rand": "R25.50",
            "currency": "ZAR",
            "note": "This is a mock estimation. Actual fare may vary."
        }
        ```
    *   Error Responses: `400 Bad Request`, `401 Unauthorized`.

---

### Drivers (`/api/drivers`)

1.  **GET /api/drivers/nearby** 🔒
    *   Description: (Mocked) Allows an authenticated 'passenger' to get a list of supposedly available drivers.
    *   Response: `200 OK` (example)
        ```json
        {
            "available_drivers": [
                {
                    "id": 2,
                    "name": "Driver One",
                    "mock_location": "Nearby Location 42",
                    "vehicle_type": "Sedan",
                    "current_status": "available"
                }
                // ... other drivers
            ]
        }
        ```
    *   Error Responses: `401 Unauthorized`, `403 Forbidden` (if not a passenger).

---

## Future Considerations (Not Implemented)

*   Database integration (e.g., PostgreSQL, MongoDB with an ORM/ODM like SQLAlchemy or MongoEngine).
*   Real-time GPS tracking (e.g., WebSockets, GeoJSON).
*   Actual fare calculation logic.
*   Driver availability management.
*   Push notifications.
*   More sophisticated error handling and logging.
*   Testing suite.
*   Food Delivery, Courier, Admin Portal modules.
```

This README provides a good overview for someone looking to understand or run this Phase 1 API.
I'll verify the file creation.
