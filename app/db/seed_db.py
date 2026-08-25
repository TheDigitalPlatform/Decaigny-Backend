import logging
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.role import Role
from app.models.user import User

logger = logging.getLogger(__name__)

SEED_ROLES = [
    {"name": "admin", "description": "Administrator with full access"},
    {"name": "user", "description": "Regular user with limited access"},
]

SEED_USERS = [
    {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "admin123",
        "role_name": "admin",
    }
]


def seed_roles(db: Session) -> None:
    for role_data in SEED_ROLES:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if existing_role:
            logger.info(f"Role '{role_data['name']}' already exists, skipping.")
            continue

        role = Role(name=role_data["name"], description=role_data["description"])
        db.add(role)
        logger.info(f"Added role: {role_data['name']}")

    db.commit()
    logger.info("Role seeding completed successfully.")


def seed_users(db: Session) -> None:
    for user_data in SEED_USERS:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_user:
            logger.info(f"User with email {user_data['email']} already exists, skipping.")
            continue

        role = db.query(Role).filter(Role.name == user_data["role_name"]).first()
        if not role:
            logger.warning(f"Role '{user_data['role_name']}' not found, skipping user {user_data['email']}.")
            continue

        user = User(
            name=user_data["name"],
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            role_id=role.id,
        )
        db.add(user)
        logger.info(f"Added user: {user_data['email']} with role '{user_data['role_name']}'")

    db.commit()
    logger.info("User seeding completed successfully.")


def seed_db(db: Session) -> None:
    logger.info("Starting database seeding...")

    seed_roles(db)
    seed_users(db)

    logger.info("Database seeding completed successfully.")