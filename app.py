import os

from flask import Flask, render_template, request, redirect, url_for, flash, session

from bs4 import BeautifulSoup

import requests

from models import db, connect_db, User, UserList, ProgressEntry, UserListBook

from forms import RegisterForm, LoginForm, NewListForm, TrackProgressForm

app = Flask(__name__)

database_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')

if database_uri is None:
    raise ValueError("SQLALCHEMY_DATABASE_URI environment variable is not set")

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'bookify-secret'

# XP dict that holds the XP values for page count milestones

XP = {
    0: 0,
    50: 10,
    100: 20,
    150: 30,
    200: 40,
    250: 50,
    300: 60,
    350: 70,
    400: 80,
    450: 90,
    500: 100,
    550: 110,
    600: 120,
    650: 130,
    700: 140,
    750: 150,
    800: 160,
    850: 170,
    900: 180,
    950: 190,
    1000: 200,
}

# Dict that holds level thresholds


def get_level_threshold(level):
    return 100 * level + 100


def determine_level(xp):
    level = 0

    while xp >= get_level_threshold(level):
        level += 1

    return level


connect_db(app)

with app.app_context():
    db.create_all()


@app.route("/")
def root():

    if "user_id" in session:

        # get most common subject if they have any books in progress
        progress = ProgressEntry.get_progress_entries(session["user_id"])

        lists = UserList.get_user_lists(session["user_id"])

        if progress:
            # Get Book Meta
            books = []

            for entry in progress:
                BASE_URL = f"https://www.googleapis.com/books/v1/volumes/{entry.book_id}"

                res = requests.get(BASE_URL)

                if res.status_code == 200:
                    data = res.json()
                    books.append(data)

            if books:
                # Get Subject
                subjects = []

                for book in books:
                    subjects.extend(book["volumeInfo"].get("categories", []))

                if subjects:
                    subject = max(set(subjects), key=subjects.count)
                    print(subject)
                    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

                    params = {"q": f"subject:{subject}", "maxResults": 8}

                    res = requests.get(BASE_URL, params=params)

                    if res.status_code == 200:
                        data = res.json()
                        books = data.get("items", [])
                        return render_template("home.html", explore=False, books=books, lists=lists)

        return render_template("home.html", explore=False, lists=lists)

    return render_template("home.html", explore=False, lists=[])


@app.route("/explore")
def explore():

    search = request.args.get('search')

    if search:

        BASE_URL = "https://www.googleapis.com/books/v1/volumes"

        params = {"q": search, "maxResults": 20}

        res = requests.get(BASE_URL, params=params)

        if res.status_code == 200:
            data = res.json()
            books = data.get("items", [])
            print(books)
            return render_template("home.html", explore=True, search=search, books=books)

        return render_template("home.html", explore=True, search=search)

    return render_template("home.html", explore=True)


@app.route("/login")
def login():

    if "user_id" in session:
        return redirect(url_for("root"))

    form = LoginForm()

    return render_template("login.html", form=form)


@app.route("/login", methods=["POST"])
def login_user():

    if "user_id" in session:
        return redirect(url_for("root"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.authenticate(email, password)

        if user:
            session["user_id"] = user.id
            flash("Welcome Back!", "success")
            return redirect(url_for("root"))

        else:
            form.email.errors = ["Invalid email/password."]

    return render_template("login.html", form=form)


@app.route("/register")
def register():

    if "user_id" in session:
        return redirect(url_for("root"))

    form = RegisterForm()

    return render_template("signup.html", form=form)


@app.route("/register", methods=["POST"])
def register_user():

    if "user_id" in session:
        return redirect(url_for("root"))

    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        email_exists = User.check_if_email_exists(email)

        if email_exists:
            form.email.errors.append(
                "Email address already exists. Please use a different email address.")
            return render_template("signup.html", form=form)

        user = User.register(email, password)

        db.session.commit()
        session["user_id"] = user.id

        flash("Welcome! Successfully Created Your Account!", "success")

        return redirect(url_for("root"))

    else:
        return render_template("signup.html", form=form)


@app.route("/logout")
def logout():
    session.pop("user_id")
    flash("You have successfully logged out!", "success")
    return redirect(url_for("root"))


@app.route("/track/<book_id>", methods=["POST"])
def track_progress_for_book(book_id):

    form = TrackProgressForm()

    if form.validate_on_submit():

        current_page = form.current_page.data

        progress = ProgressEntry.get_progress_entries(session["user_id"])

        progress_for_current_book = None

        total_pages = 0

        BASE_URL = f"https://www.googleapis.com/books/v1/volumes/{book_id}"

        res = requests.get(BASE_URL)

        if res.status_code == 200:
            data = res.json()
            total_pages = data["volumeInfo"]["pageCount"]

        for entry in progress:
            if entry.book_id == book_id:
                progress_for_current_book = entry

        if progress_for_current_book:
            progress_for_current_book.current_page = current_page
            db.session.commit()
        else:
            ProgressEntry.create(
                session["user_id"], book_id, current_page, total_pages)
            db.session.commit()

        # Check if user has reached a milestone
        current_xp = User.query.get(session["user_id"]).experience

        new_xp_value = 0

        for page_number in sorted(XP.keys()):
            if current_page >= page_number:
                new_xp_value = XP[page_number]

        # Update the user's experience
        User.query.get(session["user_id"]
                       ).experience = current_xp + new_xp_value
        db.session.commit()

        return redirect(url_for("book", book_id=book_id))

    return redirect(url_for("track_progress", book_id=book_id))


@app.route("/track/<book_id>")
def track_progress(book_id):

    progress = ProgressEntry.get_progress_entries(session["user_id"])

    progress_for_current_book = None

    for entry in progress:
        if entry.book_id == book_id:
            progress_for_current_book = entry

    form = TrackProgressForm(progress=progress_for_current_book)

    return render_template("track_progress.html", form=form, progress=progress_for_current_book, book_id=book_id)


@app.route("/book/<book_id>", methods=["POST"])
def add_to_list(book_id):

    list_id = request.form.get("list")

    if list_id:
        # check if list_id = "none"
        if list_id == "none":

            user_lists = UserList.get_user_lists(session["user_id"])

            for user_list in user_lists:
                UserListBook.query.filter_by(
                    list_id=user_list.id, book_id=book_id).delete()

            db.session.commit()

            return redirect(url_for("book", book_id=book_id))
        else:
            user_lists = UserList.get_user_lists(session["user_id"])

            for user_list in user_lists:
                UserListBook.query.filter_by(
                    list_id=user_list.id, book_id=book_id).delete()

            db.session.commit()

            UserListBook.create(list_id, book_id, "isbn")

            db.session.commit()

            return redirect(url_for("book", book_id=book_id))


@app.route("/book/<book_id>")
def book(book_id):
    BASE_URL = f"https://www.googleapis.com/books/v1/volumes/{book_id}"

    res = requests.get(BASE_URL)

    data = None

    lists = UserList.get_user_lists(session["user_id"])

    progress = ProgressEntry.get_progress_entries(session["user_id"])

    progress_for_current_book = None

    in_list = "none"

    all_books_in_lists = []

    for entry in lists:
        books = UserListBook.get_user_list_books(entry.id)
        all_books_in_lists.extend(books)

    for entry in all_books_in_lists:
        if entry.book_id == book_id:
            in_list = entry.list_id

    for entry in progress:
        if entry.book_id == book_id:
            progress_for_current_book = entry

    if res.status_code == 200:
        data = res.json()

        desc = data["volumeInfo"]["description"]

        soup = BeautifulSoup(desc, 'html.parser')

        data['volumeInfo']["description"] = soup.get_text()

    return render_template("book.html", book=data, progress=progress_for_current_book, lists=lists, in_list=in_list)


@app.route("/lists/new")
def new_list():

    form = NewListForm()

    return render_template("new_list.html", form=form)


@app.route("/lists/new", methods=["POST"])
def create_list():

    form = NewListForm()

    if form.validate_on_submit():

        name = form.name.data

        user_id = session["user_id"]

        new_list = UserList(
            name=name, user_id=user_id)

        db.session.add(new_list)
        db.session.commit()

        flash("Successfully created your list!", "success")

        return redirect(url_for("root"))

    return render_template("new_list.html", form=form)


@app.route("/list/view/<list_id>")
def list(list_id):

    list = UserList.query.get_or_404(list_id)

    books_raw = UserListBook.get_user_list_books(list_id)

    books_meta = []

    for book in books_raw:
        BASE_URL = f"https://www.googleapis.com/books/v1/volumes/{book.book_id}"

        res = requests.get(BASE_URL)

        if res.status_code == 200:
            data = res.json()
            books_meta.append(data)

    return render_template("list.html", list=list, books=books_meta)


@app.route("/profile")
def profile():

    tracked_books = ProgressEntry.get_progress_entries(session["user_id"])

    books_meta = []

    for entry in tracked_books:
        BASE_URL = f"https://www.googleapis.com/books/v1/volumes/{entry.book_id}"

        res = requests.get(BASE_URL)

        if res.status_code == 200:
            data = res.json()
            books_meta.append(data)

    xp = User.query.get(session["user_id"]).experience

    level = determine_level(xp)

    xp_to_next_level = get_level_threshold(level)

    return render_template("profile.html", experience=xp, level=level, xp_to_next_level=xp_to_next_level, books=books_meta)


@app.route("/lists/delete/<list_id>", methods=["POST"])
def delete_list(list_id):

    UserList.delete_by_id(list_id)

    return True
