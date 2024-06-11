from typing import Optional
import redis
import pickle
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import Users


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password, hashed_password):
        """
        It will check whether the password verifies against the hash.

        :param plain_password: User`s password.
        :type plain_password: str
        :param hashed_password: Hashed user's password.
        :type hashed_password: str
        :return: True or False.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Convert user's password into hash.

        :param password: User's password.
        :type password: str
        :return: Resulting hash.
        :rtype: str
        """
        return self.pwd_context.hash(password)


SECRET_KEY = "secret_key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
r = redis.Redis(host='localhost', port=6379, db=0)


async def get_user_by_email(email: str, db: Session) -> Users:
    """
    Get user by user's email with sql query.

    :param email: User's email.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: User.
    :rtype: Users
    """
    return db.query(Users).filter(Users.username == email).first()


async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    """
    Create access token.

    :param data: User's data <{'sub': username}>.
    :type data: dict
    :param expires_delta: Token's life time, default = None
    :type expires_delta: float
    :return: Encodes a claims set and returns a JWT string.
    :rtype: str
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire, "scope": "access_token"})
    encoded_access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_access_token


async def create_refresh_token(data: dict, expires_delta: Optional[float] = None):
    """
    Create refresh token.

    :param data: User's data <{'sub': username}>.
    :type data: dict
    :param expires_delta: Token's life time, default = None
    :type expires_delta: float
    :return: Encodes a claims set and returns a JWT string.
    :rtype: str
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(timezone.utc)  + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire, "scope": "refresh_token"})
    encoded_refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_refresh_token


async def get_username_from_refresh_token(refresh_token: str):
    """
    Get username frome decoded refresh token.

    :param refresh_token: User's refresh token.
    :type refresh_token: str
    :return: Username from refresh token.
    :rtype: str
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload['scope'] == 'refresh_token':
            username = payload['sub']
            return username
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
    except JWTError as error:
        print(error)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
    

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get username by decoded token, return user by function get_user_by_email.

    :param token: User's token.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: User.
    :rtype: Users
    """
    credentials_exeption = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload['scope'] == 'access_token':
            username = payload['sub']
            if username is None:
                raise credentials_exeption
        else:
            raise credentials_exeption
    except JWTError:
        raise credentials_exeption
    
    user = r.get(f"user:{username}")
    if user is None:
        user = await get_user_by_email(username, db)
        if user is None:
            raise credentials_exeption
        r.set(f"user:{username}", pickle.dumps(user))
        r.expire(f"user:{username}", 900)
    else:
        user = pickle.loads(user)
    return user


async def confirmed_email(email: str, db: Session = Depends(get_db)) -> None:
    """
    Get username by email, change field "confirmed" to True.

    :param email: User's email.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: None.
    :rtype: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


def create_email_token(data: dict):
    """
    Get username by email, change field "confirmed" to True.

    :param data: User's data.
    :type data: dict
    :return: Token created for email.
    :rtype: str
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.utcnow(), "exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """
    Get email, from decoded token.

    :param token: User's token.
    :type token: str
    :return: User's email.
    :rtype: str
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload["sub"]
        return email
    except JWTError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid token for email verification")


async def update_avatar(email, url: str, db: Session) -> Users:
    """
    Get user by email, update field "avatar" to new url.

    :param email: User's email.
    :type email: str
    :param url: Avatar's url.
    :type url: str
    :param db: The database session.
    :type db: Session
    :return: User.
    :rtype: Users
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user