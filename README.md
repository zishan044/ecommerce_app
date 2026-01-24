# E-Commerce API Backend

Production-ready REST API built with **FastAPI**, **PostgreSQL**, and **SQLModel**. Full authentication, shopping cart, order management, and Stripe payments integration.

## Tech Stack

- **Framework**: FastAPI (async, auto-generated OpenAPI docs)
- **Database**: PostgreSQL with SQLModel ORM + Alembic migrations
- **Auth**: JWT (python-jose) + bcrypt password hashing
- **Payments**: Stripe webhook integration
- **Caching**: Redis (performance optimization)
- **Server**: Uvicorn ASGI

## Core Features

| Feature | Tech |
|---------|------|
| User authentication & OAuth2 | JWT tokens, bcrypt, OAuth2PasswordFlow |
| Product catalog | CRUD ops, pagination, filtering |
| Shopping cart | Persistent user sessions |
| Order management | Full lifecycle tracking, status updates |
| Payment processing | Stripe API, webhook handlers |
| Database migrations | Alembic versioning |

## API Routes

- `POST /auth/login` – OAuth2 JWT token generation
- `GET/POST /products` – Product listing & creation
- `GET/POST /users` – User management
- `GET/POST /cart` – Shopping cart operations
- `POST /orders` – Order creation & tracking
- `POST /payments/create-checkout-session` – Stripe checkout
- `POST /payments/webhook` – Webhook signature verification

## Architecture Highlights

✓ **Type-safe**: Full type hints with Pydantic/SQLModel schemas
✓ **Testable**: Database tests with isolated temporary schemas
✓ **Scalable**: Async throughout, connection pooling, Redis support
✓ **Secure**: Password hashing, JWT auth, Stripe webhook verification
✓ **Documented**: Auto-generated interactive API docs at `/docs`

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@localhost/ecommerce
alembic upgrade head
python main.py  # runs tests, then uvicorn app:app
```

## Python Backend Skills Demonstrated

- Advanced async patterns & dependency injection (FastAPI Depends)
- ORM with SQLModel (hybrid approach: Pydantic + SQLAlchemy)
- Database schema versioning & migrations (Alembic)
- Production auth patterns (JWT, OAuth2, password security)
- Third-party API integration (Stripe) with webhook verification
- Error handling & HTTP status codes
- Request/response validation with automatic OpenAPI schemas
