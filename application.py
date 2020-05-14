import requests
from flask import Flask, session, render_template, request, logging, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://vfrqdxwcyogetg:96cccefe8951dcc704c73fd70bc30b1e3b63348c118668de0bdf9fec3e259106@ec2-54-157-78-113.compute-1.amazonaws.com:5432/d6vbal80o42meg")
db = scoped_session(sessionmaker(bind=engine))

# Makes CSS dynamic by clearing browser cache ------------

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

# ------------------------------------------

# App routes ------------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/2")
def index2():
    return render_template("index2.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["POST", "GET"])
def login():

    if request.method == "POST":
        userinput = request.form.get("userinput")
        password = request.form.get("password")
        print(userinput)
        print(password)
        if userinput == '' and password == '':
            return render_template("login.html", errormessage="Enter Username and Password")
        elif userinput == '':
            return render_template("login.html", errormessage="Enter Username or Email")
        elif password == '':
            return render_template("login.html", errormessage="Enter Password")            
        else:
            tableusername = db.execute("SELECT username FROM users WHERE username=:userinput or email=:userinput", {"userinput":userinput}).fetchone()
            passworddata = db.execute("SELECT password FROM users WHERE username=:userinput or email=:userinput", {"userinput":userinput}).fetchone()
            
            # WHYYYYYYYYYYYYYYYYYYYYY
            for username in tableusername:
                username = username  
            for db_password in passworddata:
                if sha256_crypt.verify(password, db_password):
                    session['username'] = username
                    return redirect(url_for('books', username=username))
                else:
                    return render_template("login.html", errormessage="Incorrect Password")            

    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/submitted", methods=["POST", "GET"])
def submitted():
    if request.method == "GET":
        return "Form not submitted."
    if request.method == "POST":
       
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        secure_password = sha256_crypt.encrypt(str(password))

        if email == '' or username == '' or password == '' or confirmation == '':
            return render_template("signup.html", errormessage="Some fields left blank")            
    
        checkuser = db.execute("SELECT * FROM users WHERE username = :username or email = :email", {"username":username, "email":email}) 
        if checkuser.rowcount > 0:
            return render_template("signup.html", errormessage="User already exists.")            

        if password == confirmation:
            db.execute("INSERT INTO users(email, username, password) VALUES(:email,:username,:password)",
                                                                            {"email":email, "username":username, "password":secure_password})
            db.commit()
            session['username'] = username
            return redirect(url_for('books', username=username))
        else:
            return render_template("signup.html", errormessage="Passwords do not match")            

@app.route("/api")
def api():
    return render_template("api.html")

@app.route("/loggedin_api")
def loggedin_api():
    return render_template("api2.html")

@app.route("/api/<book_isbn>")
def isbn_api(book_isbn):

    bookinfo = db.execute("SELECT * FROM books WHERE isbn = :book_isbn", {"book_isbn":book_isbn}) 
    if bookinfo.rowcount == 0:
        return render_template("error.html", message="Error 404: Friendly Books does not have any books with this ISBN :(.")
    else:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "3QNyHosgpPsjYGGh7ahwA", "isbns": book_isbn})    
        data = res.json()
        rating_count = data['books'][0]['ratings_count']
        average_rating = data['books'][0]['average_rating']
        for book in bookinfo:
            return jsonify({
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "isbn": book.isbn,
                "review_count": rating_count,
                "average_score": average_rating
            })

@app.route("/loggedin_api/<book_isbn>")
def isbn_api2(book_isbn):

    bookinfo = db.execute("SELECT * FROM books WHERE isbn = :book_isbn", {"book_isbn":book_isbn}) 
    if bookinfo.rowcount == 0:
        return render_template("error.html", message="Error 404: Friendly Books does not have any books with this ISBN :(.")
    else:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "3QNyHosgpPsjYGGh7ahwA", "isbns": book_isbn})    
        data = res.json()
        rating_count = data['books'][0]['ratings_count']
        average_rating = data['books'][0]['average_rating']
        for book in bookinfo:
            return jsonify({
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "isbn": book.isbn,
                "review_count": rating_count,
                "average_score": average_rating
            })

@app.route("/books", methods=["POST", "GET"])
def books():
    #uses the current session username to display username on different route page
    bookresults = ''
    searchterm = 'Peace'
    results = 0
    if request.method == "POST":
        searchterm = request.values.get("searcher")
    bookresults = db.execute("SELECT isbn, title, author FROM books WHERE UPPER(ISBN) LIKE UPPER('%"+searchterm+"%') or UPPER(TITLE) LIKE UPPER('%"+searchterm+"%') or UPPER(AUTHOR) LIKE UPPER('%"+searchterm+"%')")     
    results = bookresults.rowcount

    return render_template("bookpage.html", username=session['username'], bookresults=bookresults, query=searchterm, results=results) 


@app.route("/books/<book_isbn>", methods=["POST", "GET"])
def singlebooks(book_isbn):
    if request.method == "POST":
        if db.execute("SELECT * FROM reviews WHERE isbn = :book_isbn AND username =:username", {"book_isbn":book_isbn, "username":session['username']}).rowcount != 0:
            return render_template("error.html", message="Oops. Looks like you have already left a review for this book!")
        else:
            reviewtext = request.form.get("reviewtext")
            rating = request.form.get("rating")
            db.execute("INSERT INTO reviews(username, isbn, review, rating) VALUES(:username,:isbn,:review,:rating)",
                                                                                {"username":session['username'], "isbn":book_isbn, "review":reviewtext, "rating":rating})
            db.commit()

    #Book Rating
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "3QNyHosgpPsjYGGh7ahwA", "isbns": book_isbn})    
    data = res.json()
    rating_count = data['books'][0]['ratings_count']
    average_rating = data['books'][0]['average_rating']
    #Show other reviews
    bookinfo = db.execute("SELECT * FROM books WHERE isbn = :book_isbn", {"book_isbn":book_isbn})       
    if bookinfo.rowcount == 0:
        return render_template("error.html", message="Error 404: Friendly Books does not have any books with this ISBN :(.")
    else:
        #ONCE AGAIN WHYYY
        for book in bookinfo:
            reviews = db.execute("SELECT username, review, rating FROM reviews WHERE isbn = :book_isbn", {"book_isbn":book_isbn})     
            
        return render_template("bookinfo.html", ISBN=book_isbn, TITLE=book.title, AUTHOR=book.author, YEAR=book.year, reviews=reviews, rating_count=rating_count, average_rating=average_rating)