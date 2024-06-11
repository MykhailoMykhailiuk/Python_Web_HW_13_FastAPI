from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.database.models import Contacts, Users
from src.schemas import ContactCreate, ContactUpdate


async def get_contacts(skip: int, limit: int, user: Users, db: Session):
    """
    Display a list of contacts for a specific user with specified pagination parameters.

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param user: The user to retrieve contacts for.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: A list of Conatcts.
    :rtype: List[Conatcts]
    """
    return db.query(Contacts).filter(Contacts.user_id == user.id).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user: Users, db: Session):
    """
    Display a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param user: The user to retrieve the contact for.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Conatcts | None
    """
    return db.query(Contacts).filter(and_(Contacts.id == contact_id, Contacts.user_id == user.id)).first()


async def create_contact(body: ContactCreate, user: Users, db: Session):
    """
    Creates a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: ContactCreate
    :param user: The user to create the contact for.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: The newly created contact.
    :rtype: Contacts
    """

    contact = Contacts(**body.dict(), user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, user: Users, db: Session):
    """
    Removes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param user: The user to remove the contact for.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: The removed contact, or None if it does not exist.
    :rtype: Contacts | None
    """
    contact = db.query(Contacts).filter(and_(Contacts.id == contact_id, Contacts.user_id == user.id)).first()
    if contact:

        db.delete(contact)
        db.commit()
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, user: Users, db: Session):
    """
    Updates a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated data for the contact.
    :type body: ContactUpdate
    :param user: The user to update the contact for.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: The updated contact, or None if it does not exist.
    :rtype: Contacts | None
    """
    contact = db.query(Contacts).filter(and_(Contacts.id == contact_id, Contacts.user_id == user.id)).first()
    if contact:
        contact.name = body.name
        contact.lastname = body.lastname
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.additional = body.additional
        db.commit()
    return contact


async def get_birthdays(user: Users, db: Session):
    """
    Display a list of contacts that have a birthday in 7 days period for a specific user.

    :param user: The user to find the contacts birthday for.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: A list of contacts that have a birthday in 7 days period.
    :rtype: List[Contacts]
    """
    today = datetime.today().date()
    offset = today + timedelta(days=7)
    result = db.query(Contacts).filter(and_(Contacts.user_id == user.id, Contacts.birthday.between(today, offset))).all()
    return result


async def search_contacts(query: str, user: Users, db: Session):
    """
    Display a list of contacts for a specific user with specific sql query.

    :param query: Sql query string.
    :type query: str
    :param user: The user to find the contacts.
    :type user: Users
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contacts]
    """
    result = db.query(Contacts).filter(and_(
            Contacts.user_id == user.id,
            or_(
                (Contacts.name.ilike(f"%{query}%")),
                (Contacts.lastname.ilike(f"%{query}%")),
                (Contacts.email.ilike(f"%{query}%"))
            ))).all()
    return result


