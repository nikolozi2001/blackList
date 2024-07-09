from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from config import navigation_items
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure the database URI
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blackList.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=False, nullable=False)
    surname = db.Column(db.String(30), unique=False, nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"Users('{self.name}', '{self.surname}', '{self.username}')"


class Posts(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(1000), unique=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"Posts('{self.title}', '{self.content}')"


@app.route("/")
def home():
    return render_template("index.html", navigation_items=navigation_items)


@app.route("/about")
def about():
    return render_template("about.html", navigation_items=navigation_items)


@app.route("/workers")
def workers():
    return render_template("workers.html", navigation_items=navigation_items)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return f"თქვენ სისტემაში შესული ხართ როგორც {username}"
        else:
            return "მომხმარებლის სახელი ან პაროლი არასწორია"
    return render_template("login.html", navigation_items=navigation_items)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        surname = request.form["surname"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if Users.query.filter_by(username=username).first():
            return "ასეთი მომხმარებლის სახელი უკვე არსებობს"
        elif password != confirm_password:
            return "პაროლები არ ემთხვევა"
        else:
            hashed_password = generate_password_hash(password)
            new_user = Users(
                name=name, surname=surname, username=username, password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            return f"დარეგისტრირებულია ახალი მომხმარებელი: {username}"
    return render_template("register.html", navigation_items=navigation_items)


if __name__ == "__main__":
    db.create_all()  # Ensure the database tables are created
    app.run(debug=True)
