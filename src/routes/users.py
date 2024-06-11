from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.database.models import Users
from src.repository import auth as repository_auth
from src.config.config import settings1
from src.schemas import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", 
            response_model=User, 
            description="No more than 10 requests per minute",
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_users_me(current_user: User = Depends(repository_auth.get_current_user)):
    """
    Display the user.

    :param current_user: User to display.
    :type current_user: User
    :return: User.
    :rtype: User
    """
    return current_user


@router.patch('/avatar', 
              response_model=User, 
              description="No more than 10 requests per minute",
              dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def update_avatar_user(file: UploadFile = File(), current_user: User = Depends(repository_auth.get_current_user),
                             db: Session = Depends(get_db)):
    
    """
    Update avatar for specific user.

    :param file: File to set as avatar for user.
    :type file: UploadFile
    :param current_user: The user to avatar's update contacts for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: User with updated avatar.
    :rtype: User
    """
        
    cloudinary.config(
        cloud_name=settings1.cloudinary_name,
        api_key=settings1.cloudinary_api_key,
        api_secret=settings1.cloudinary_api_secret,
        secure=True
    )

    r = cloudinary.uploader.upload(file.file, public_id=f'api/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'api/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_auth.update_avatar(current_user.username, src_url, db)
    return user
