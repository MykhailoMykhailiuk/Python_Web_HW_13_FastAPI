from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.database.models import Contacts, Users
from src.schemas import ContactCreate, ContactUpdate


async def get_contacts(skip: int, limit: int, user: Users, db: Session):
    return db.query(Contacts).filter(Contacts.user_id == user.id).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user: Users, db: Session):
    return db.query(Contacts).filter(and_(Contacts.id == contact_id, Contacts.user_id == user.id)).first()


async def create_contact(body: ContactCreate, user: Users, db: Session):
    contact = Contacts(**body.dict(), user_id=user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, user: Users, db: Session):
    contact = db.query(Contacts).filter(and_(Contacts.id == contact_id, Contacts.user_id == user.id)).first()
    if contact:

        db.delete(contact)
        db.commit()
    return contact


async def update_contact(contact_id: int, body: ContactUpdate, user: Users, db: Session):
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
    today = datetime.today().date()
    offset = today + timedelta(days=7)
    result = db.query(Contacts).filter(and_(Contacts.user_id == user.id, Contacts.birthday.between(today, offset))).all()
    return result


async def search_contacts(query: str, user: Users, db: Session):
    result = db.query(Contacts).filter(and_(
            Contacts.user_id == user.id,
            or_(
                (Contacts.name.ilike(f"%{query}%")),
                (Contacts.lastname.ilike(f"%{query}%")),
                (Contacts.email.ilike(f"%{query}%"))
            ) )).all()
    return result


