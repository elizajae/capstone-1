import unittest
from flask import Flask
from app import app, db
from models import User


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_root_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_root_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login_route(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_register_route(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)

    def test_explore_route(self):
        response = self.client.get('/explore')
        self.assertEqual(response.status_code, 200)

    def test_profile_route(self):
        test_user = User(email='test@example.com', password='testpassword')
        db.session.add(test_user)
        db.session.commit()

        with self.client.session_transaction() as session:
            session['user_id'] = test_user.id

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        # self.assertIn(b'Profile', response.data)

    def test_track_progress_route(self):
        book_id = 'your_test_book_id'

        test_user = User(email='test@example.com', password='testpassword')
        db.session.add(test_user)
        db.session.commit()

        with self.client.session_transaction() as session:
            session['user_id'] = test_user.id

        response = self.client.get(f'/track/{book_id}')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
