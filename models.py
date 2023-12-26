from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    experience = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "experience": self.experience,
        }

    @classmethod
    def check_if_email_exists(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def register(cls, email, password):

        hashed = bcrypt.generate_password_hash(password)
        hashed_utf8 = hashed.decode("utf8")

        user = cls(email=email, password=hashed_utf8)
        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, email, password):
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False


class UserListBook(db.Model):
    __tablename__ = "user_list_books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    list_id = db.Column(db.Integer, db.ForeignKey('user_list.id'))
    book_id = db.Column(db.String, nullable=False)
    isbn = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "list_id": self.list_id,
            "book_id": self.book_id,
            "isbn": self.isbn
        }

    @classmethod
    def create(cls, list_id, book_id, isbn):
        user_list_book = cls(list_id=list_id, book_id=book_id, isbn=isbn)
        db.session.add(user_list_book)
        return user_list_book

    @classmethod
    def get_user_list_books(cls, list_id):
        return cls.query.filter_by(list_id=list_id).all()


class UserList(db.Model):
    __tablename__ = "user_list"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name
        }

    @classmethod
    def create(cls, user_id, name):
        user_list = cls(user_id=user_id, name=name)
        db.session.add(user_list)
        return user_list

    @classmethod
    def get_user_lists(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()


class ProgressEntry(db.Model):
    __tablename__ = "progress_entries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.String, nullable=False)
    current_page = db.Column(db.Integer, nullable=False)
    total_pages = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "current_page": self.current_page,
            "total_pages": self.total_pages
        }

    @classmethod
    def create(cls, user_id, book_id, current_page, total_pages):
        progress_entry = cls(user_id=user_id, book_id=book_id,
                             current_page=current_page, total_pages=total_pages)
        db.session.add(progress_entry)
        return progress_entry

    @classmethod
    def get_progress_entries(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()


class ExperienceEntry(db.Model):
    __tablename__ = "experience_entries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    experience = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "experience": self.experience,
            "date": self.date
        }

    @classmethod
    def create(cls, user_id, experience, date):
        experience_entry = cls(
            user_id=user_id, experience=experience, date=date)
        db.session.add(experience_entry)
        return experience_entry

    @classmethod
    def get_experience_entries(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()


def connect_db(app):
    db.app = app
    db.init_app(app)
