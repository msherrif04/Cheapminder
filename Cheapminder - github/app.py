from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect
import pandas
from sqlalchemy import create_engine, func
import random
from send_mail import send_mail
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)

ENV = 'prod'

if ENV == 'dev':
    app.debug=True
    app.config['SQLALCHEMY_DATABASE_URI']=''
else:
    app.debug=False
    app.config['SQLALCHEMY_DATABASE_URI']='postgresql://thxzasyvgardkv:66a4de6b933ac5927a3a2964157458e4de3c7ce188b21036ac6825a8fdbc3449@ec2-52-6-77-239.compute-1.amazonaws.com:5432/d2s4fhhjr9980l?sslmode=require'

app.config ['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db= SQLAlchemy (app)

class Highlight(db.Model):

    __tablename__ = 'highlights'
    
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.Text(), nullable=False)
    author = db.Column(db.String, nullable=False)
    book = db.Column(db.String, nullable=False)

    def __init__(self, quote, author, book):
        self.quote= quote
        self.author= author
        self.book= book


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)

    def __init__(self, username, email):
        self.email = email
        self.username = username



@app.route('/', methods=["GET" , "POST"])
def index():
    global book_list
    global random_quote

    book_list = db.session.query(func.count(Highlight.book),Highlight.book).group_by(Highlight.book).all()
    #Creating Random Quote from table
    random_quote = generate_random_quote()

    if request.method == "GET":
        pass

    if request.method == "POST":
        quote = request.form.get('quote')
        author = request.form.get('author')
        book = request.form.get('book')
        if quote and author and book:
            try:
                highlight = Highlight(quote, author, book)
                db.session.add(highlight)
                db.session.commit()
            except Exception as e:
                return render_template('index.html', book_list = book_list, random_quote = random_quote, sign_up_status = str(e))
        else:
            error = "One or more Fields is empty, please try again"
            return render_template('index.html', book_list = book_list, random_quote = random_quote, sign_up_status = error)
    return render_template('index.html', book_list = book_list, random_quote = random_quote)



@app.route('/highlights')
def highlights():
        highlights = Highlight.query.all()

        #Creating Random Quote from table
        random_quote = generate_random_quote()
        return render_template('highlights.html', highlights = Highlight.query.all(), random_quote = random_quote)

@app.route('/import_csv', methods=["GET","POST"])

def import_csv():

    if request.method == "GET":
        pass
    if request.method == "POST":
        file = request.files['file']
        try:
            df = pandas.read_csv(file,sep=',')
            engine = create_engine('postgresql://postgres:sharrafa5@localhost/Quotes_Generator')
            df.to_sql('highlights', engine, if_exists='append', index=False)
        except Exception:
            error = "Oops, something went wrong there. Kindly make sure your file is a csv with three columns; 'quote, author, book' and try again"
            return render_template('index.html', book_list = book_list, random_quote = random_quote, sign_up_status = error)

    return render_template('highlights.html', highlights = Highlight.query.all())

@app.route('/highlights_by_book/<book>')
def highlights_by_book(book):
    #Creating Random Quote from table
    random_quote = generate_random_quote()
    
    highlights_by_book =  Highlight.query.filter_by(book = book).all()

    return render_template('highlights_by_book.html', highlights = highlights_by_book, book = book, random_quote = random_quote)

@app.route('/sign_up_success', methods=["POST"])
def sign_up_success():

    book_list = db.session.query(func.count(Highlight.book),Highlight.book).group_by(Highlight.book).all()

    #Creating Random Quote from table
    random_quote = generate_random_quote()

    if request.method == "POST":
        username = request.form.get('first_name')
        email = request.form.get('email')

        #validation to make sure fields are not empty and taken
        if email or username:
            if User.query.filter_by(email = email).count() > 0:
                error = "You are already signed up."
                return render_template('index.html', sign_up_status = error, book_list = book_list, random_quote = random_quote)
            else:
                user = User(username, email)
                db.session.add(user)
                db.session.commit()
                success = "You have been signed up successfully"
                return render_template('index.html', sign_up_status=success, book_list = book_list, random_quote = random_quote)
        else:
            sign_up_status="First name or Email field cannot be blank"
            return render_template('index.html', sign_up_status=sign_up_status, book_list = book_list, random_quote = random_quote)

def generate_random_quote():
    #Creating Random Quote from table
    length_table = Highlight.query.count()
    random_id = random.randint(1,length_table)
    random_quote = Highlight.query.get(random_id)
    return (random_quote)

def email_daily_quote():

    #Creating Random Quote from table
    random_quote = generate_random_quote()
    quote = random_quote.quote
    author = random_quote.author
    book = random_quote.book

    #generating list of emails in database
    users = User.query.order_by(User.email).all()
    users = [user.email for user in users]

    #Sending random quote to every user in list
    email = users
    send_mail (email,quote, author, book)


scheduler = BackgroundScheduler()
scheduler.add_job(func=email_daily_quote, trigger="interval", seconds=86400)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    app.run() 