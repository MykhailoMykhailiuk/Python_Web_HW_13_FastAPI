from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.database.models import Users
from src.schemas import Contact, ContactCreate, ContactUpdate
from src.repository import contacts as repository_contacts
from src.repository import auth as repository_auth

router = APIRouter(prefix='/contacts', tags=["contacts"])


@router.post("/", response_model=Contact, 
             status_code=status.HTTP_201_CREATED,
             description='No more than 10 requests per minute',
             dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def create_contact(body: ContactCreate, 
                         db: Session = Depends(get_db),
                         current_user: Users = Depends(repository_auth.get_current_user)):
    return await repository_contacts.create_contact(body, current_user, db)


@router.get("/", response_model=List[Contact], 
            description='No more than 10 requests per minute', 
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(skip: int = 0, 
                        limit: int = 100, 
                        current_user: Users = Depends(repository_auth.get_current_user),
                        db: Session = Depends(get_db)):
    contacts = await repository_contacts.get_contacts(skip, limit, current_user, db)
    return contacts


@router.get("/{contact_id}", response_model=Contact)
async def read_contact(contact_id: int, 
                       db: Session = Depends(get_db),
                       current_user: Users = Depends(repository_auth.get_current_user)):
    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(contact_id: int, 
                         body: ContactUpdate, 
                         db: Session = Depends(get_db),
                         current_user: Users = Depends(repository_auth.get_current_user)):
    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=Contact)
async def remove_contact(contact_id: int, 
                         db: Session = Depends(get_db),
                         current_user: Users = Depends(repository_auth.get_current_user)):
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/birthdays/", response_model=List[Contact])
async def get_birthdays(db: Session = Depends(get_db),
                        current_user: Users = Depends(repository_auth.get_current_user)):
    return await repository_contacts.get_birthdays(current_user, db)


@router.get("/search/", response_model=List[Contact])
async def search_contatcs(query,
                          current_user: Users = Depends(repository_auth.get_current_user),
                          db: Session = Depends(get_db)):
    contact = await repository_contacts.search_contacts(query, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found"')
    return contact