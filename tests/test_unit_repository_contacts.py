import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.database.models import Contacts, Users
from src.schemas import Contact, ContactCreate, ContactUpdate
from src.repository.contacts import (
    get_contacts,
    get_contact,
    create_contact,
    remove_contact,
    update_contact,
    get_birthdays,
    search_contacts
)


class TestNotes(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = Users(id=1)

    async def test_get_contacts(self):
        contacts = [Contacts(),]
        self.session.query().filter().offset().limit().all.return_value = contacts
        result = await get_contacts(skip=0, limit=10, user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = Contacts()
        self.session.query().filter().first.return_value = contact
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_get_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_create_contact(self):
        body = ContactCreate(
            name='John', 
            lastname='Smith',
            email='smith@gmail.com',
            phone='9876543210',
            birthday='2000-02-03',
            additional='Unknown man'
        )
        result = await create_contact(body=body, user=self.user, db=self.session)
        self.assertEqual(body.name, result.name)
        self.assertEqual(body.lastname, result.lastname)
        self.assertEqual(body.email, result.email)
        self.assertEqual(body.phone, result.phone)
        self.assertEqual(body.birthday, result.birthday)
        self.assertEqual(body.additional, result.additional)
        self.assertTrue(hasattr(result, "id"))

    async def test_remove_contact_found(self):
        contact = Contacts()
        self.session.query().filter().first.return_value = contact
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result, contact)

    async def test_remove_contact_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await remove_contact(contact_id=1, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_update_contact_found(self):
        contact = ContactCreate(
            name='John', 
            lastname='Smith',
            email='smith@gmail.com',
            phone='9876543210',
            birthday='2000-02-03',
            additional='Unknown man'
        )

        body = ContactUpdate(
            name='John', 
            lastname='Smith',
            email='smith@gmail.com',
            phone='9876543210',
            birthday='2000-02-03',
            additional='Best friend'
        )

        self.session.query().filter().first.return_value = contact
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertEqual(contact, result)

    async def test_update_contact_not_found(self):

        body = ContactUpdate(
            name='July', 
            lastname='Smith',
            email='smith@gmail.com',
            phone='9876543210',
            birthday='2000-02-03',
            additional='Best friend'
        )

        self.session.query().filter().first.return_value = None
        self.session.commit.return_value = None
        result = await update_contact(contact_id=1, body=body, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_get_birthdays(self):
        contacts = [
            ContactCreate(
                name="John",
                lastname="Smith",
                email="smith@gmail.com",
                phone="9876543210",
                birthday=datetime.date.today() + datetime.timedelta(days=3),
                additional="Just friend",
            ),
        ]
        self.session.query().filter().all.return_value = contacts
        result = await get_birthdays(user=self.user, db=self.session)
        self.assertEqual(result, contacts)

    async def test_get_birthdays_not_found(self):
        self.session.query().filter().all.return_value = None
        result = await get_birthdays(user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_seach_contacts_found(self):
        query = 'Smith'
        contact = [
            ContactCreate(
                name="John",
                lastname="Smith",
                email="smith@gmail.com",
                phone="9876543210",
                birthday='2000-02-03',
                additional="Just friend",
            )
        ]
        self.session.query().filter().all.return_value = contact
        result = await search_contacts(query=query, user=self.user, db=self.db)
        self.assertEqual(result, contact)

    async def test_seach_contacts_not_found(self):
        query = ''
        self.session.query().filter().all.return_value = None
        result = await search_contacts(query=query, user=self.user, db=self.db)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()