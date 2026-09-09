"""Операции над учётными записями пользователей."""

from datetime import timedelta
from typing import Optional

from sqlmodel import Session, func, select

from app.core.audit import log_action
from app.core.config import settings
from app.core.problems import APIProblem, Problems
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.audit_log import EntityType
from app.models.user import User, UserRole
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserUpdate


class UserService:
    """Создание, чтение и изменение учётных записей."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[User]:
        """Вернуть пользователя по адресу электронной почты."""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Вернуть пользователя по идентификатору."""
        return self.session.get(User, user_id)

    def create_user(self, user_data: UserCreate, created_by: User) -> User:
        """Создать учётную запись.

        Args:
            user_data: Адрес, пароль и роль новой учётной записи.
            created_by: Администратор, выполняющий операцию.

        Returns:
            Созданная учётная запись.

        Raises:
            APIProblem: Если адрес уже зарегистрирован.
        """
        if self.get_by_email(user_data.email):
            raise APIProblem(
                Problems.EMAIL_ALREADY_EXISTS,
                f"Email {user_data.email} is already registered",
            )

        new_user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role,
        )

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        log_action(
            session=self.session,
            user_id=created_by.id,
            action="create_user",
            entity_type=EntityType.user,
            entity_id=new_user.id,
            meta={"created_email": new_user.email, "role": new_user.role.value},
        )

        return new_user

    def authenticate(self, credentials: UserLogin) -> Token:
        """Проверить учётные данные и выпустить токен доступа.

        Args:
            credentials: Адрес и пароль пользователя.

        Returns:
            Токен доступа со схемой Bearer.

        Raises:
            APIProblem: Если учётные данные неверны либо запись деактивирована.
        """
        user = self.get_by_email(credentials.email)

        if not user or not verify_password(credentials.password, user.password_hash):
            raise APIProblem(
                Problems.INVALID_CREDENTIALS,
                "Email or password is incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise APIProblem(
                Problems.USER_DEACTIVATED,
                "User account is deactivated",
            )

        access_token = create_access_token(
            data={"user_id": user.id, "role": user.role.value},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        log_action(
            session=self.session,
            user_id=user.id,
            action="login",
            entity_type=EntityType.user,
            entity_id=user.id,
        )

        return Token(access_token=access_token, token_type="bearer")

    def list_users(
        self,
        offset: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
    ) -> tuple[list[User], int]:
        """Вернуть страницу учётных записей.

        Args:
            offset: Смещение от начала коллекции.
            limit: Размер страницы.
            role: Отбор по роли пользователя.

        Returns:
            Учётные записи текущей страницы и общее количество записей.
        """
        conditions = [User.role == role] if role else []

        total = self.session.exec(
            select(func.count()).select_from(User).where(*conditions)
        ).one()

        statement = (
            select(User).where(*conditions).order_by(User.id).offset(offset).limit(limit)
        )

        return list(self.session.exec(statement).all()), total

    def update_user(self, user_id: int, user_data: UserUpdate, updated_by: User) -> User:
        """Изменить роль или состояние учётной записи.

        Args:
            user_id: Идентификатор изменяемой учётной записи.
            user_data: Изменяемые атрибуты; неуказанные поля не изменяются.
            updated_by: Администратор, выполняющий операцию.

        Returns:
            Изменённая учётная запись.

        Raises:
            APIProblem: Если пользователь не найден либо администратор
                пытается деактивировать собственную учётную запись.
        """
        user = self.get_by_id(user_id)

        if not user:
            raise APIProblem(
                Problems.USER_NOT_FOUND,
                f"User {user_id} does not exist",
            )

        changes = user_data.model_dump(exclude_unset=True)

        if changes.get("is_active") is False and user.id == updated_by.id:
            raise APIProblem(
                Problems.ACCESS_DENIED,
                "Administrators cannot deactivate their own account",
            )

        for field, value in changes.items():
            setattr(user, field, value)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        log_action(
            session=self.session,
            user_id=updated_by.id,
            action="update_user",
            entity_type=EntityType.user,
            entity_id=user.id,
            meta=changes,
        )

        return user
