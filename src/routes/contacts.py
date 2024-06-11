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
    """
    Creates a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: ContactCreate
    :param db: The database session.
    :type db: Session
    :param current_user: The user to create the contact for.
    :type current_user: Users
    :return: The newly created contact.
    :rtype: Contacts
    """
    return await repository_contacts.create_contact(body, current_user, db)


@router.get("/", response_model=List[Contact], 
            description='No more than 10 requests per minute', 
            dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def read_contacts(skip: int = 0, 
                        limit: int = 100, 
                        current_user: Users = Depends(repository_auth.get_current_user),
                        db: Session = Depends(get_db)):
    """
    Display a list of contacts for a specific user with specified pagination parameters.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param current_user: The user to retrieve contacts for.
    :type current_user: Users
    :param db: The database session.
    :type db: Session
    :return: A list of Conatcts.
    :rtype: List[Conatcts]
    """
    contacts = await repository_contacts.get_contacts(skip, limit, current_user, db)
    return contacts


@router.get("/{contact_id}", response_model=Contact)
async def read_contact(contact_id: int, 
                       db: Session = Depends(get_db),
                       current_user: Users = Depends(repository_auth.get_current_user)):
    
    """
    Display a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param current_user: The user to retrieve the contact for.
    :type current_user: Users
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Conatcts | None
    """

    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(contact_id: int, 
                         body: ContactUpdate, 
                         db: Session = Depends(get_db),
                         current_user: Users = Depends(repository_auth.get_current_user)):
    
    """
    Updates a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated data for the contact.
    :type body: ContactUpdate
    :param db: The database session.
    :type db: Session
    :param current_user: The user to update the contact for.
    :type current_user: Users
    :return: The updated contact, or None if it does not exist.
    :rtype: Contacts | None
    """
        
    contact = await repository_contacts.update_contact(contact_id, body, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", response_model=Contact)
async def remove_contact(contact_id: int, 
                         db: Session = Depends(get_db),
                         current_user: Users = Depends(repository_auth.get_current_user)):
    
    """
    Removes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param db: The database session.
    :type db: Session
    :param current_user: The user to remove the contact for.
    :type current_user: Users
    :return: The removed contact, or None if it does not exist.
    :rtype: Contacts | None
    """
        
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/birthdays/", response_model=List[Contact])
async def get_birthdays(db: Session = Depends(get_db),
                        current_user: Users = Depends(repository_auth.get_current_user)):
    """
    Display a list of contacts that have a birthday in 7 days period for a specific user.

    :param db: The database session.
    :type db: Session
    :param current_user: The user to find the contacts birthday for.
    :type current_user: Users
    :return: A list of contacts that have a birthday in 7 days period.
    :rtype: List[Contacts]
    """
    return await repository_contacts.get_birthdays(current_user, db)


@router.get("/search/", response_model=List[Contact])
async def search_contatcs(query,
                          current_user: Users = Depends(repository_auth.get_current_user),
                          db: Session = Depends(get_db)):
    
    """
    Display a list of contacts for a specific user with specific sql query.

    :param query: Sql query string.
    :type query: str
    :param current_user: The user to find the contacts.
    :type current_user: Users
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contacts]
    """
        
    contact = await repository_contacts.search_contacts(query, current_user, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Contact not found"')
    return contact