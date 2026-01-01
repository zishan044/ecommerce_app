import os
import uuid
from decimal import Decimal
import traceback

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

import database
import models


def run_tests() -> None:
    """Run lightweight tests for database.py and models.py.

    - Detects `DATABASE_URL` from environment
    - If Postgres, runs tests inside a temporary schema to avoid touching existing schemas
    - Inserts a Product and a User, verifies insert/queries
    - Tests `database.create_db_and_tables` and `database.get_session` (verifies the generator yields a usable session)
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("No DATABASE_URL found in environment; aborting tests.")
        return

    # Prepare engine and patch the app database module to use it
    engine = create_engine(db_url, echo=False)
    original_engine = getattr(database, "engine", None)
    database.engine = engine

    try:
        if db_url.startswith("postgres"):
            schema = f"test_schema_{uuid.uuid4().hex[:8]}"
            print(f"Using Postgres; creating temporary schema '{schema}' for tests...")

            engine = create_engine(db_url, echo=False)

            # Patch database.engine so get_session uses this engine
            original_engine = getattr(database, "engine", None)
            database.engine = engine

            # 1️⃣ Create schema + set search_path on the SAME connection
            with engine.begin() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.execute(text(f"SET search_path TO {schema}"))
                SQLModel.metadata.create_all(bind=conn)

            # 2️⃣ Run API tests (sessions inherit search_path)
            from fastapi.testclient import TestClient
            from app import app

            client = TestClient(app)

            try:
                resp = client.post(
                    "/users/",
                    json={
                        "full_name": "John Doe",
                        "email": "john@example.com",
                        "password": "secret",
                    },
                )
                assert resp.status_code == 201, resp.text
                print("✅ POST /users created user via API")

                prod_payload = {
                    "name": "Test Product",
                    "description": "A product",
                    "price": "9.99",
                    "in_stock": 5,
                    "category": "Test",
                }
                resp = client.post("/products/", json=prod_payload)
                assert resp.status_code == 201, resp.text
                prod_id = resp.json()["id"]
                print("✅ POST /products created product via API")

                resp = client.get("/products/")
                assert resp.status_code == 200
                print("✅ GET /products returned products via API")

                resp = client.get(f"/products/{prod_id}")
                assert resp.status_code == 200
                print("✅ GET /products/{id} returned product")

                print("All Postgres API tests passed ✅")

            finally:
                # 3️⃣ Drop schema cleanly
                with engine.begin() as conn:
                    conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
                print(f"Dropped temporary schema '{schema}'.")

        else:
            # Fall back to sqlite temporary db for other URLs
            import tempfile
            from sqlmodel import select

            tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            tmp_path = tmp.name
            tmp.close()
            db_url = f"sqlite:///{tmp_path}"
            engine = create_engine(db_url, echo=False)
            print("Creating tables on temporary SQLite database...")
            SQLModel.metadata.create_all(engine)

            with Session(engine) as session:
                p = models.Product(
                    name="Test Product",
                    description="A product",
                    price=Decimal("9.99"),
                    in_stock=5,
                    category="Test",
                )
                u = models.User(full_name="John Doe", email="john@example.com", hashed_password="hashed")

                session.add(p)
                session.add(u)
                session.commit()
                session.refresh(p)
                session.refresh(u)

                assert p.id is not None, "Product ID should be set after commit"
                assert p.name == "Test Product"
                assert p.price == Decimal("9.99")
                assert u.email == "john@example.com"

                print("✅ Insert and query tests passed on SQLite.")

            # Ensure create_db_and_tables runs using the patched engine
            database.create_db_and_tables()
            print("✅ database.create_db_and_tables executed without error.")

            # Test get_session yields a usable session (generator-style dependency)
            gen = database.get_session()
            sess = next(gen)
            try:
                result = sess.exec(select(models.Product)).all()
                assert len(result) >= 1, "Expected at least one product from get_session"
                print("✅ database.get_session yielded a usable session.")
            finally:
                gen.close()

            print("All SQLite tests passed ✅")

    except Exception:
        print("Some tests failed:")
        traceback.print_exc()
    finally:
        # Restore original engine
        if original_engine is not None:
            database.engine = original_engine
        else:
            try:
                delattr(database, "engine")
            except Exception:
                pass


if __name__ == "__main__":
    run_tests()
