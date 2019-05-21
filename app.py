from app_utils import *
from flask import Flask, render_template, request, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import time
import sqlite3
import os



app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = URI
#db.init_app(app)
Session(app)
#sess = sessionmaker(bind=engine)
#session = sess()

def is_logged_in():
    if 'username' not in session:
        return False 
    else:
        return True

def assert_login():
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            if not is_logged_in():
                session['messages'] = "Please login to view that page"
                return redirect(url_for('home')) 
            else:
                return f(*args, **kwargs)
        wrapped_f.__name__ = f.__name__
        return wrapped_f
    return wrap   



@app.route('/', methods=["GET", "POST"])
def home(msg=''):
	if request.method == 'GET':
		if 'messages' in session:
			error_message = session['messages']
			session.pop('messages')
			return render_template('home.jinja2', msg=error_message)
		if msg != '':
			return render_template('home.jinja2', msg=msg)
		else:
			return render_template('home.jinja2')
	elif request.method == 'POST':
		return try_login(request.form)
	
	


@app.route('/register', methods=["GET", "POST"])
def register():
	if request.method == 'GET':
		return render_template('register.jinja2')
	else:
		created, usn = account_creation_handler(request.form)
		if created:
			return success(usn)
		else:
			return render_template("register.jinja2", err_msg = "Sorry, but the username " + usn + " is already in use. Please pick another one.")


@app.route("/success")
def success(username):
    return render_template("success.html", username=username)

@app.route('/logout')
@assert_login()
def logout():
	name = session['username']
	session.pop('username')
	return render_template('goodbye.jinja2', name=name)


@app.route("/welcome")
@assert_login()
def welcome():
	return render_template('welcome.jinja2', username=session['username'])



#required functions
def try_login(form):
    username = form.get("username")
    password = form.get("password")
    db_entry = Users.query.filter(Users.username == username).first()
    if db_entry is None:
        session['messages'] = f"No username {username} found"
        return redirect(url_for('home'))
    elif db_entry.password != password:
        session['messages'] = "Incorrect password"
        return redirect(url_for('home'))
    else:
        session['username'] = username
        return welcome()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()

if __name__ == '__main__':
    Base.query = db.query_property()
    with app.app_context():
        #db.create_all()
        Base.metadata.create_all(bind=engine)

    app.run(host='0.0.0.0', debug=True)