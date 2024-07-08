from flask import Flask, render_template, request, redirect, url_for
from config import navigation_items
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


db = SQLAlchemy()

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=False, nullable=False)
    surname = db.Column(db.String(30), unique=False, nullable=False)
    personalid = db.Column(db.Integer(11), unique=True, nullable=True)

    def __repr__(self):
        return f"Users('{self.name}', '{self.surname}', '{self.personalid}')"


users = {
    'admin': 'admin',
    'nikakachibaia': 'general126'
}


@app.route("/")
def home():
    return render_template("index.html", navigation_items=navigation_items)


@app.route("/about")
def about():
    return render_template("about.html", navigation_items=navigation_items)


@app.route("/workers")
def workers():
    return render_template("workers.html", navigation_items=navigation_items)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            return f'თქვენ სისტემაში შესული ხართ როგორც {username}'
        else:
            return 'მომხმარებლის სახელი ან პაროლი არასწორია'
    return render_template("login.html", navigation_items=navigation_items)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if username in users:
            return 'ასეთი მომხმარებლის სახელი უკვე არსებობს'
        elif password != confirm_password:
            return 'პაროლები არ ემთხვევა'
        else:
            users[username] = password
            return f'დარეგისტრირებულია ახალი მომხმარებელი: {username}'
    return render_template("register.html", navigation_items=navigation_items)


if __name__ == "__main__":
    app.run(debug=True)
