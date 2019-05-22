from sql_schemas import *
from flask import Flask, render_template, request, session, redirect
import time
import sqlite3
import os
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import scoped_session, sessionmaker
import datetime
from passlib.hash import sha256_crypt
import json


def validate_password(password, record):
    return sha256_crypt.verify(password + salt(), record.password)

def now():
    return datetime.datetime.now()

def cur_time():
    return str_now()[11:]

def str_now():
    return str(now())[:19]

def cur_day():
    return str_now()[:10]

def one_month_ago():
    return str(datetime.datetime.now()  - datetime.timedelta(days=30))[:19]

def account_creation_handler(form):
    username = form.get("username")
    password = form.get("password")
    email = form.get("email")
    if username_taken(username):
        success = False
    else:
        create_account(username, password, email)
        success = True
    return success, username


def username_taken(username):
    res = Users.query.filter(Users.username == username).first()
    if res == None:
        return False
    return True

def create_account(username, password, email):
    u = Users(username=username, password=sha256_crypt.encrypt(password + salt()), email=email)
    db.add(u)
    db.commit()


def delete_hourly_record(record_id, user_id):
    obj = Hourly.query.filter(and_(Hourly.id == record_id, Hourly.user_id == user_id)).first()
    if obj is None:
        return f"Failed to find object with record id {record_id}"
    else:
        db.delete(obj)
        db.commit()
        return f"Successfully deleted record id {record_id}!"

def delete_daily_record(record_id, user_id):
    obj = Daily.query.filter(and_(Daily.id == record_id, Daily.user_id == user_id)).first()
    if obj is None:
        return f"Failed to find object with record id {record_id}"
    else:
        db.delete(obj)
        db.commit()
        return f"Successfully deleted record id {record_id}!"


def type_or_none(val, cast):
    if val == '':
        return None
    else:
        return cast(val)

def is_day(day):
    try:
        datetime.datetime.strptime(day, '%Y-%m-%d')
        return True
    except:
        return False

def is_time(t):
    try:
        datetime.datetime.strptime(t, '%H:%M:%S')
        return True
    except:
        return False

def interpret_meal_status(s):
    return 0 if s == 'before' else 1

def validate_daily_data(form, user_id, make_record=True, check_exists=True):
    day = form.get('day')
    weight = form.get('weight')
    steps = form.get('steps')
    calories = form.get('calories')
    if not is_day(day):
        return f"Malformed date {day}"

    if len(Daily.query.filter(Daily.timestamp == day).all()) > 0 and check_exists:
        return f"Already have an entry for {day}. Please visit url /edit/daily/ to ammend this input."

    for val in [steps, weight, calories]:
        try:
            type_or_none(val, int)
        except:
            return f"Malformed integer {val}"
    # data checked out
    if make_record:
        d = Daily(user_id = user_id, timestamp = day, steps = type_or_none(steps, int), 
                    calories = type_or_none(calories, int), weight = type_or_none(weight, int))
        db.add(d)
        db.commit()

def validate_hourly_data(form, user_id, make_record=True, check_exists=True):
    day = form.get('day')
    t = form.get('time').strip()
    blood_sugar = form.get('blood_sugar')
    notes = form.get('notes')
    meal_status = interpret_meal_status(form.get('meal_status'))

    if not is_day(day):
        return f"Malformed date {day}"
    
    if not is_time(t):
        return f"Malformed time {t}"

    if len(Hourly.query.filter(Hourly.timestamp == f"{day} {t}").all()) > 0 and check_exists:
        return f"Already have an entry for {day} {t}. Please visit url /edit/hourly/ to ammend this input."

    try:
        type_or_none(blood_sugar, int)
    except:
        return f"Malformed blood_sugar (integer required): {blood_sugar}"

    if make_record:
        h = Hourly(user_id=user_id, timestamp=f"{day} {t}", blood_sugar=type_or_none(blood_sugar, int),
                    symptoms=notes, meal_status = meal_status)
        db.add(h)
        db.commit()


def salt():
    with open('configs.json', 'r') as fin:
        return json.load(fin)['salt']

def handle_hourly_record_update(form, user_id, hourly_record_id):
    valid_data = validate_hourly_data(form, user_id, make_record=False, check_exists=False)
    if isinstance(valid_data, str):
        return valid_data
    else:
        change_log = {}
        record = Hourly.query.filter(and_(Hourly.id == hourly_record_id, Hourly.user_id == user_id)).first()
        datetime = f"{form.get('day')} {form.get('time')}"
        if datetime != record.timestamp:
            change_log['timestamp'] = [datetime, record.timestamp]
        for old, new, name in zip([int(form.get('blood_sugar')), 0 if form.get('meal_status') == "before" else 1, form.get('notes')],
                                    [record.blood_sugar, record.meal_status, record.symptoms],
                                    ['blood sugar', 'meal status', 'notes']):
            if old != new:
                change_log[name] = [old, new]
        # Hourly.query.filter(and_(Hourly.id == hourly_record_id), Hourly.user_id == user_id).update({'timestamp': datetime, 'blood_sugar': int(form.get('blood_sugar')), 'symptoms': form.get('notes')})
        record = Hourly.query.filter(and_(Hourly.id == hourly_record_id, Hourly.user_id == user_id)).first()
        record.blood_sugar = int(form.get('blood_sugar'))
        db.commit()
        record = Hourly.query.filter(and_(Hourly.id == hourly_record_id, Hourly.user_id == user_id)).first()
        record.timestamp = datetime
        db.commit()
        record = Hourly.query.filter(and_(Hourly.id == hourly_record_id, Hourly.user_id == user_id)).first()
        record.symptoms = form.get('notes')
        db.commit()
        record = Hourly.query.filter(and_(Hourly.id == hourly_record_id, Hourly.user_id == user_id)).first()
        record.meal_status = 0 if form.get('meal_status') == 'before' else 1
        db.flush()
        db.commit()
        return change_log


def handle_daily_record_update(form, user_id, daily_record_id):
    valid_data = validate_daily_data(form, user_id, make_record=False, check_exists=False)
    record = Daily.query.filter(and_(Daily.id == daily_record_id, Daily.user_id == user_id)).first()
    if isinstance(valid_data, str):
        return valid_data
    record = Daily.query.filter(and_(Daily.id == daily_record_id, Daily.user_id == user_id)).first()
    record.timestamp = form.get('day')
    db.commit()
    record = Daily.query.filter(and_(Daily.id == daily_record_id, Daily.user_id == user_id)).first()
    record.weight = type_or_none(form.get('weight'), int)
    db.commit()
    record = Daily.query.filter(and_(Daily.id == daily_record_id, Daily.user_id == user_id)).first()
    record.steps = type_or_none(form.get('steps'), int)
    db.commit()
    record = Daily.query.filter(and_(Daily.id == daily_record_id, Daily.user_id == user_id)).first()
    record.calories = type_or_none(form.get('calories'), int)
    db.commit()
    return {}
