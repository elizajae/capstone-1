from flask import Flask, render_template, request, redirect, url_for, flash, session

from bs4 import BeautifulSoup

import requests

from models import db, connect_db, User, UserList, ProgressEntry, UserListBook

from forms import RegisterForm, LoginForm, NewListForm, TrackProgressForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2329@localhost/bookify-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'bookify-secret'

connect_db(app)

with app.app_context():
    db.create_all()


@app.route("/")
def root():

    lists = UserList.get_user_lists(session["user_id"])

    return render_template("home.html", explore=False, lists=lists)


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

        return redirect(url_for("book", book_id=book_id))

    return redirect(url_for("track_progress", book_id=book_id))


@app.route("/track/<book_id>")
def track_progress(book_id):
    form = TrackProgressForm()

    progress = ProgressEntry.get_progress_entries(session["user_id"])

    progress_for_current_book = None

    for entry in progress:
        if entry.book_id == book_id:
            progress_for_current_book = entry

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
