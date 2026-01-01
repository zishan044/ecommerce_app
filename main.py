import os
import tempfile
from decimal import Decimal
import traceback

from sqlmodel import SQLModel, create_engine, Session, select

import database
import models


def run_tests() -> None:
    """Run lightweight tests for database.py and models.py.

    - Creates a temporary SQLite database file
    - Creates tables from `models`
    - Inserts a Product and a User
    - Verifies they can be queried back
    - Tests `database.create_db_and_tables` and `database.get_session`
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_path = tmp.name
    tmp.close()
    db_url = f"sqlite:///{tmp_path}"
    engine = create_engine(db_url, echo=False)

    print("Creating tables on temporary database...")
    SQLModel.metadata.create_all(engine)

    # Monkeypatch database.engine so database.get_session and create_db_and_tables use our test engine
    original_engine = getattr(database, "engine", None)
    database.engine = engine

    try:
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

            print("✅ Insert and query tests passed.")

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
            # Close the generator to exit the context manager inside get_session
            gen.close()

        print("All tests passed ✅")

    except Exception:
        print("Some tests failed:")
        traceback.print_exc()
    finally:
        # Restore original engine (if any) and remove temp file
        if original_engine is not None:
            database.engine = original_engine
        else:
            # Remove attribute to restore original state if it didn't exist
            try:
                delattr(database, "engine")
            except Exception:
                pass
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


if __name__ == "__main__":
    run_tests()
