from app_utils import *
from visuals import *
from flask import Flask, render_template, request, url_for
from flask_session import Session
from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime

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


@app.route("/welcome", methods=["GET", "POST"])
@assert_login()
def welcome():
    if request.form.get('submit_button') == None:
        w_chart = weight_chart(Daily.query.filter(and_(Daily.user_id == session['user_id'], Daily.timestamp >= one_month_ago())).order_by(desc(Daily.timestamp)))
        bps = blood_pies(Hourly.query.filter(and_(Hourly.user_id == session['user_id'], Hourly.timestamp >= one_month_ago())))
        bbs = blood_bars(Hourly.query.filter(and_(Hourly.user_id == session['user_id'], Hourly.timestamp >= one_month_ago())))
        return render_template('welcome.jinja2', username=session['username'], weight=w_chart, pre_pie=bps[0], post_pie=bps[1],
                                pre_bar=bbs[0], post_bar=bbs[1])
    else:
        action = request.form.get('submit_button')
        if action == "daily":
            return redirect(url_for('daily_entry'))
        elif action == "hourly":
            return redirect(url_for("blood_entry"))
        elif action == "edit_data":
            return redirect(url_for("edit"))
        else:
            return redirect(url_for('welcome'))


@app.route('/edit/', methods=["GET", "POST"])
@assert_login()
def edit():
    if request.method == "GET":
        return render_template('edit_home.jinja2')
    else:
        form = request.form
        if 'hourly' in form:
            return redirect(url_for('edit_hourly'))
        elif 'daily' in form:
            return redirect(url_for('edit_daily'))
        else:
            return redirect(url_for('edit'))

@app.route('/edit/hourly/', methods=["POST", "GET"])
@assert_login()
def edit_hourly():
    if request.method == "GET":
        records = Hourly.query.filter(Hourly.user_id == session['user_id']).order_by(desc(Hourly.timestamp))
        return render_template('edit_hourly.jinja2', records=records)
    else:
        if "edit" in request.form:
            return redirect(url_for('edit_hourly_record', id=request.form.get("edit")))


@app.route('/edit/daily/', methods=["GET", "POST"])
@assert_login()
def edit_daily():
    if request.method == "GET":
        records = Daily.query.filter(Daily.user_id == session['user_id']).order_by(desc(Daily.timestamp))
        return render_template('edit_daily.jinja2', records=records)
    else:
        if "edit" in request.form:
            return redirect(url_for('edit_daily_record', id=request.form.get("edit")))

@app.route('/edit/hourly/<int:id>/', methods = ["GET", "POST"])
@assert_login()
def edit_hourly_record(id):
    if request.method == "GET":
        record = Hourly.query.filter(Hourly.id == id).first()
        if record is None:
            return render_template('edit_hourly_record.jinja2', msg="No record found", record="", cls="failure")
        elif 'messages' in session:
            err_msg = session['messages']
            session.pop('messages')
            msg_class = "failure" if err_msg.find("Successfully") == -1 else "success"
            return render_template('edit_hourly_record.jinja2', record=record, msg=err_msg, cls=msg_class)
        else:
            return render_template('edit_hourly_record.jinja2', record=record)
    else:
        updated_form = request.form
        result = handle_hourly_record_update(request.form, session['user_id'], id)
        if isinstance(result, str):
            session['messages'] = result
        else:
            session['messages'] = f"Successfully edited a daily entry for {request.form.get('day')} {request.form.get('time')}!<br>\
                Changes are: <br>"
            for key in result:
                if key == 'meal status':
                    new = 'before' if result[key][0] == 0 else 'after'
                    old = 'before' if new == 'after' else 'after'
                else:
                    new = result[key][0]
                    old = result[key][1]
                session['messages'] += f"{key} from \"{old}\" to \"{new}\" <br>"
        return redirect(url_for('edit_hourly_record', id=id))


@app.route('/edit/daily/<int:id>')
@assert_login()
def edit_daily_record(id):
    record = Daily.query.filter(Daily.id == id).first()
    if record is None:
        return render_template('FILL ME IN')

@app.route('/enter/daily/', methods=["GET", "POST"])
@assert_login()
def daily_entry():
    if request.method == "GET":
        today = cur_day()
        if 'messages' in session:
            err_msg = session['messages']
            session.pop('messages')
            message_class = 'success' if err_msg.find('Success') > -1 else 'failure'
        else:
            message_class = 'success'
            err_msg = ''
        return render_template('daily_entry.jinja2', cur_day=today, message = err_msg, message_class = message_class)
    else:
        result = validate_daily_data(request.form, session['user_id'])
        if isinstance(result, str):
            session['messages'] = result
        else:
            session['messages'] = f"Successfully added a daily entry for {request.form.get('day')}!"
        return redirect(url_for('daily_entry'))

@app.route('/entry/blood_sugar/', methods=["GET", "POST"])
@assert_login()
def blood_entry():
    if request.method == "GET":
        today = cur_day()
        t = cur_time()
        if 'messages' in session:
            err_msg = session['messages']
            session.pop('messages')
            message_class = 'success' if err_msg.find('Success') > -1 else 'failure'
        else:
            message_class = 'success'
            err_msg = ''
        return render_template('blood_sugar_entry.jinja2', cur_day=today, cur_time=t, message = err_msg, message_class = message_class)
    else:
        result = validate_hourly_data(request.form, session['user_id'])
        if isinstance(result, str):
            session['messages'] = result
        else:
            session['messages'] = f"Successfully added a blood sugar reading for {request.form.get('day')} {request.form.get('time')}!"
        return redirect(url_for('blood_entry'))

#required functions
def try_login(form):
    username = form.get("username")
    password = form.get("password")
    db_entry = Users.query.filter(Users.username == username).first()
    if db_entry is None:
        session['messages'] = f"No username {username} found"
        return redirect(url_for('home'))
    #elif sha256_crypt.verify(password, db_entry.password):
    elif not validate_password(password, db_entry):
        session['messages'] = "Incorrect password"
        return redirect(url_for('home'))
    else:
        session['user_id'] = db_entry.id
        session['username'] = username
        return redirect(url_for('welcome'))


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()


Base.query = db.query_property()

with app.app_context():
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
