from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from libgravatar import Gravatar

from src.database.db import get_db
from src.database.models import Users
from src.schemas import User, UserBase, CreateUser, RequestEmail
from src.repository import auth as repository_auth
from src.servises.email import send_email


hash_handler = repository_auth.Hash()
security = HTTPBearer()

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(body: CreateUser,
                 backround_tasks: BackgroundTasks,
                 request: Request,
                 db: Session = Depends(get_db)):
    
    """
    Create new user, sent the confirmation email.

    :param body: The data for the user to create.
    :type body: CreateUser
    :param backround_tasks: Tasks that will be called after a response has been sent to the client.
    :type backround_tasks: BackgroundTasks
    :param request: parameter for making HTTP requests.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Registered user, registration cinfirmation string.
    :rtype: dict
    """
    
    avatar = None
    try:
        g = Gravatar(body.username)
        avatar = g.get_image()
    except Exception as e:
        print(e)

    exist_user = await repository_auth.get_user_by_email(body.username, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exist')
    new_user = Users(username=body.username, password=hash_handler.get_password_hash(body.password), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    backround_tasks.add_task(send_email, new_user.username, request.base_url)
    return {'user': new_user.username, 'detail': 'User successfully created. Check your email for confirmation.'} 


@router.post('/login')
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Function to user login, with user's username, email confirmed and password verifycation.

    :param body: Data for user's login.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session.
    :type db: Session
    :return: Access token, refresh token and token type.
    :rtype: dict
    """
    user = await repository_auth.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username')
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email not confirmed')
    if not hash_handler.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid password')
    
    access_token = await repository_auth.create_access_token(data={'sub': user.username})
    refresh_token = await repository_auth.create_refresh_token(data={'sub': user.username})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Update refresh token for user.

    :param credentials: HTTP authorization credentials.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :return: Access token, refresh token and token type.
    :rtype: dict
    """
    token = credentials.credentials
    username = await repository_auth.get_username_from_refresh_token(token)
    user = db.query(Users).filter(Users.username == username).first()
    if user.refresh_token != token:
        user.refresh_token = None
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await repository_auth.create_access_token(data={"sub": username})
    refresh_token = await repository_auth.create_refresh_token(data={"sub": username})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Check the email confirmation for user.

    :param token: Token.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Email confirmation.
    :rtype: dict
    """
    email = await repository_auth.get_email_from_token(token)
    user = await repository_auth.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_auth.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Check the email confirmation for user, if user is not confirmed send the email confirmation to users email.

    :param body: User's email.
    :type body: RequestEmail
    :param backround_tasks: Tasks that will be called after a response has been sent to the client.
    :type backround_tasks: BackgroundTasks
    :param request: parameter for making HTTP requests.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Email confirmation.
    :rtype: dict
    """
    user = await repository_auth.get_user_by_email(body.email, db)

    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}
