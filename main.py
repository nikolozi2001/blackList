from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import navigation_items
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from functools import wraps
from flask_migrate import Migrate

app = Flask(__name__)

# Configure the database URI
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blackList.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecretkey"  # Set a secret key for session management
app.config["SESSION_TYPE"] = "filesystem"  # Specify the session type
Session(app)  # Initialize the session extension

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=False, nullable=False)
    surname = db.Column(db.String(30), unique=False, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    posts = db.relationship("Posts", backref="author", lazy=True)

    def __repr__(self):
        return f"Users('{self.name}', '{self.surname}', '{self.username}')"


class Posts(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=False, nullable=False)
    surname = db.Column(db.String(30), unique=False, nullable=False)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"Posts('{self.title}', '{self.content}')"


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("გთხოვთ ჯერ სისტემაში შეხვიდეთ.", "warning")
            return redirect(url_for("login"))

        user = Users.query.filter_by(username=session["username"]).first()

        if user is None:
            flash("მომხმარებელი არ მოიძებნა", "danger")
            return redirect(url_for("home"))

        if not user.is_admin:
            flash("დაშვებული არ არის", "danger")
            return redirect(url_for("home"))

        return f(*args, **kwargs)

    return decorated_function


class LoginForm(FlaskForm):
    username = StringField("მომხმარებლის სახელი", validators=[DataRequired()])
    password = PasswordField("პაროლი", validators=[DataRequired()])
    submit = SubmitField("შესვლა")


class RegisterForm(FlaskForm):
    name = StringField("სახელი", validators=[DataRequired()])
    surname = StringField("გვარი", validators=[DataRequired()])
    username = StringField("მომხმარებლის სახელი", validators=[DataRequired()])
    password = PasswordField("პაროლი", validators=[DataRequired()])
    confirm_password = PasswordField(
        "დაადასტურეთ პაროლი",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("რეგისტრაცია")


@app.route("/admin")
@admin_required
def admin():
    users = Users.query.all()
    posts = Posts.query.all()
    return render_template(
        "admin.html", users=users, posts=posts, navigation_items=navigation_items
    )


@app.route("/admin/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):
    user = Users.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("მომხმარებელი წაშლილია", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete_post/<int:post_id>")
@admin_required
def delete_post(post_id):
    post = Posts.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        flash("პოსტი წაშლილია", "success")
    return redirect(url_for("admin"))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("გთხოვთ ჯერ სისტემაში შეხვიდეთ.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def home():
    return render_template("index.html", navigation_items=navigation_items)


@app.route("/about")
def about():
    return render_template("about.html", navigation_items=navigation_items)


@app.route("/workers")
@login_required
def workers():
    posts = Posts.query.all()  # Fetch all posts from the database
    return render_template(
        "workers.html", posts=posts, navigation_items=navigation_items
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("მომხმარებლის სახელი ან პაროლი არასწორია", "danger")
    return render_template("login.html", navigation_items=navigation_items, form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        surname = form.surname.data
        username = form.username.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        if Users.query.filter_by(username=username).first():
            flash("ასეთი მომხმარებლის სახელი უკვე არსებობს", "danger")
        elif password != confirm_password:
            flash("პაროლები არ ემთხვევა", "danger")
        else:
            hashed_password = generate_password_hash(password)
            new_user = Users(
                name=name, surname=surname, username=username, password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            flash(f"დარეგისტრირებულია ახალი მომხმარებელი: {username}", "success")
            return redirect(url_for("login"))
    return render_template(
        "register.html", navigation_items=navigation_items, form=form
    )


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    db.create_all()  # Ensure the database tables are created
    app.run(debug=True)
