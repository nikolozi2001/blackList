from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import navigation_items
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from functools import wraps
from flask_migrate import Migrate
from flask_wtf.file import FileField, FileAllowed
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

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
    photo = db.Column(db.String(100), nullable=True)  # New column for photo
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"Posts('{self.title}', '{self.content}')"


class PostForm(FlaskForm):
    name = StringField("სახელი", validators=[DataRequired()])
    surname = StringField("გვარი", validators=[DataRequired()])
    title = StringField("სათაური", validators=[DataRequired()])
    content = TextAreaField("აღწერა", validators=[DataRequired()])
    photo = FileField("ფოტო", validators=[FileAllowed(["jpg", "png", "jpeg"])])
    submit = SubmitField("დამატება")


class EditUserForm(FlaskForm):
    name = StringField("სახელი", validators=[DataRequired()])
    surname = StringField("გვარი", validators=[DataRequired()])
    username = StringField("მომხმარებლის სახელი", validators=[DataRequired()])
    submit = SubmitField("განახლება")


class EditPostForm(FlaskForm):
    name = StringField("სახელი", validators=[DataRequired()])
    surname = StringField("გვარი", validators=[DataRequired()])
    title = StringField("სათაური", validators=[DataRequired()])
    content = TextAreaField("აღწერა", validators=[DataRequired()])
    submit = SubmitField("რედაქტირება")


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


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    search_query = request.args.get("search")
    if search_query:
        users = Users.query.filter(
            (Users.name.like(f"%{search_query}%"))
            | (Users.surname.like(f"%{search_query}%"))
            | (Users.username.like(f"%{search_query}%"))
        ).all()
        posts = Posts.query.filter(
            (Posts.name.like(f"%{search_query}%"))
            | (Posts.surname.like(f"%{search_query}%"))
            | (Posts.title.like(f"%{search_query}%"))
            | (Posts.content.like(f"%{search_query}%"))
        ).all()
    else:
        users = Users.query.all()
        posts = Posts.query.all()
    return render_template(
        "admin.html", users=users, posts=posts, navigation_items=navigation_items
    )


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("გთხოვთ ჯერ სისტემაში შეხვიდეთ.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/admin/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):
    user = Users.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("მომხმარებელი წაშლილია", "success")
    return redirect(url_for("admin"))


@app.route("/workers/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Posts.query.get_or_404(post_id)
    user = Users.query.filter_by(username=session["username"]).first()
    if post.author.id != user.id and not user.is_admin:
        flash("თქვენ არ შეგიძლიათ ამ პოსტის წაშლა", "danger")
        return redirect(url_for("workers"))

    db.session.delete(post)
    db.session.commit()
    flash("პოსტი წაშლილია", "success")
    return redirect(url_for("workers"))


@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = Users.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.name = form.name.data
        user.surname = form.surname.data
        user.username = form.username.data
        db.session.commit()
        flash("მომხმარებელი განახლებულია", "success")
        return redirect(url_for("admin"))
    return render_template(
        "edit_user.html", form=form, navigation_items=navigation_items
    )


@app.route("/admin/edit_post/<int:post_id>", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    post = Posts.query.get_or_404(post_id)
    form = EditPostForm(obj=post)
    if form.validate_on_submit():
        post.name = form.name.data
        post.surname = form.surname.data
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("პოსტი განახლებულია", "success")
        return redirect(url_for("admin"))
    return render_template(
        "edit_post.html", form=form, navigation_items=navigation_items
    )


@app.route("/admin/delete_post/<int:post_id>", methods=["POST"])
@admin_required
def delete_post_admin(post_id):
    post = Posts.query.get_or_404(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        flash("პოსტი წაშლილია", "success")
    return redirect(url_for("admin"))


@app.route("/view_post/<int:post_id>")
def view_post(post_id):
    post = Posts.query.get_or_404(post_id)
    return render_template(
        "view_post.html", post=post, navigation_items=navigation_items
    )


@app.route("/")
def home():
    return render_template("index.html", navigation_items=navigation_items)


@app.route("/about")
def about():
    return render_template("about.html", navigation_items=navigation_items)


# Set the folder to save uploaded files
app.config["UPLOAD_FOLDER"] = "static/uploads"


@app.route("/workers", methods=["GET", "POST"])
@login_required  # or any decorator you use to protect this route
def workers():
    form = PostForm()
    search_query = request.args.get("search")

    if form.validate_on_submit():
        user = Users.query.filter_by(
            username=session["username"]
        ).first()  # Assuming logged-in user
        if form.photo.data:
            photo_file = form.photo.data
            # Generate a unique filename using UUID and current timestamp
            unique_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_filename = secure_filename(
                f"{unique_id}_{timestamp}_{photo_file.filename}")
            photo_file.save(os.path.join(
                app.config["UPLOAD_FOLDER"], photo_filename))
        else:
            photo_filename = None

        new_post = Posts(
            name=form.name.data,
            surname=form.surname.data,
            title=form.title.data,
            content=form.content.data,
            photo=photo_filename,  # Save the photo filename to the database
            user_id=user.id,
        )
        db.session.add(new_post)
        db.session.commit()
        flash("პოსტი წარმატებით დაემატა", "success")
        return redirect(url_for("workers"))

    if search_query:
        posts = Posts.query.filter(
            (Posts.name.like(f"%{search_query}%"))
            | (Posts.surname.like(f"%{search_query}%"))
            | (Posts.title.like(f"%{search_query}%"))
            | (Posts.content.like(f"%{search_query}%"))
        ).all()
    else:
        posts = Posts.query.all()

    return render_template(
        "workers.html", posts=posts, form=form, navigation_items=navigation_items
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
            session["is_admin"] = user.is_admin
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
            flash(
                f"დარეგისტრირებულია ახალი მომხმარებელი: {username}", "success")
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
