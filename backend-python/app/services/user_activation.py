"""
User Activation Service — activates or deactivates a user based on
the agentic risk assessment decision.

Called by the guardrails layer after APPROVE / REJECT:
  - APPROVE → activate_user(user_id)   → sets User.isActive = True
  - REJECT  → deactivate_user(user_id) → sets User.isActive = False
  - REVIEW  → no action (human analyst decides later)
"""
from contextlib import contextmanager
from database.database import SessionLocal
from model.model import User


@contextmanager
def _get_db():
    """Context manager that always closes the session, even on error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def activate_user(user_id: str) -> dict:
    """
    Set User.isActive = True for the given user_id.
    Called when the agentic system produces an APPROVE decision.

    Returns a status dict for audit logging.
    Raises ValueError if user not found.
    """
    with _get_db() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            user.isActive = True
            db.commit()
            db.refresh(user)

            print(f"[UserActivation] User {user_id} activated (isActive=True)")
            return {
                "user_id": str(user.id),
                "username": user.username,
                "isActive": user.isActive,
                "action": "ACTIVATED",
            }
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to activate user {user_id}: {e}")


def deactivate_user(user_id: str) -> dict:
    """
    Set User.isActive = False for the given user_id.
    Called when the agentic system produces a REJECT decision.

    Returns a status dict for audit logging.
    Raises ValueError if user not found.
    """
    with _get_db() as db:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            user.isActive = False
            db.commit()
            db.refresh(user)

            print(f"[UserActivation] User {user_id} deactivated (isActive=False)")
            return {
                "user_id": str(user.id),
                "username": user.username,
                "isActive": user.isActive,
                "action": "DEACTIVATED",
            }
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to deactivate user {user_id}: {e}")
