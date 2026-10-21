# Cab Booking Platform — Python Backend

A Phase-1 backend engineering project based on the supplied project screenshots. It uses **FastAPI, PostgreSQL, SQLAlchemy, JWT authentication, and Docker Compose**.

## Features
- Rider/driver registration and login with JWT access tokens
- Password hashing
- Driver profile creation and availability toggle
- Fare estimate using `₹50 base fare + ₹14 per kilometre`
- Ride requests, driver acceptance, ride status updates and history
- Reviews for completed rides
- Interactive API documentation at `/docs`
- PostgreSQL database and Docker-based local setup

> This is an educational starter implementation, not a production ride-hailing service. Before public deployment, add migrations, automated tests, rate limiting, refresh-token/revocation strategy, audit logging, payment integration, location/geospatial matching and stronger secret management.

## Run with Docker (recommended)
1. Install Docker Desktop.
2. Extract this ZIP and open a terminal in the `cab-booking-platform` folder.
3. Copy `.env.example` to `.env` and change `SECRET_KEY` to a long random value.
4. Run:

   ```bash
   docker compose up --build
   ```

5. Open **http://localhost:8000/docs**.

Stop with `Ctrl+C`; run `docker compose down` to stop containers. To also delete the local database volume, run `docker compose down -v` (this permanently deletes its data).

## Run locally without Docker
Requires Python 3.12+ and PostgreSQL. Create a database/user, set environment variables, then:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

Set `DATABASE_URL` to your PostgreSQL connection string and set `SECRET_KEY`, then run:

```bash
uvicorn app.main:app --reload
```

## API endpoint summary

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register rider or driver |
| POST | `/auth/login` | Login and receive JWT |
| GET | `/auth/me` | Current account details |
| POST | `/drivers/profile` | Create driver profile |
| PATCH | `/drivers/availability` | Set driver availability |
| GET | `/drivers/available` | List available drivers |
| POST | `/rides/estimate` | Estimate fare |
| POST | `/rides/request` | Request a ride (rider) |
| POST | `/rides/{ride_id}/accept` | Accept a ride (driver) |
| PATCH | `/rides/{ride_id}/status` | Update ride status |
| GET | `/rides/history` | View current user's ride history |
| POST | `/reviews` | Review a completed ride |
| GET | `/reviews/driver/{driver_id}` | List driver reviews |

## Quick API test flow
1. In `/docs`, register a rider with role `rider`, and copy the returned `access_token`.
2. Click **Authorize** and enter the token (or `Bearer <token>` if prompted).
3. Use `/rides/estimate`, then `/rides/request`.
4. Register a second account with role `driver`, log in, and authorize with that token.
5. Create a driver profile using `/drivers/profile`, then set availability to `true`.
6. Accept the ride ID, set status to `ongoing`, then `completed`.
7. Log in as the rider again and submit a review for that ride.

## Fare formula
`Estimated fare = base fare + (distance in km × rate per km)`

Example: 10 km = ₹50 + (10 × ₹14) = **₹190**.

## Database tables
- `users`: accounts and roles
- `drivers`: vehicle details and availability
- `rides`: pickup, destination, distance, fare, status and participants
- `reviews`: ride rating and comment

## Project layout

```text
cab-booking-platform/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── security.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Important notes
- Ride distance is provided by the API caller in this starter version; it is not automatically calculated from maps.
- The project does not charge payments or use live GPS.
- Set a strong secret key and review security before deploying anywhere public.
