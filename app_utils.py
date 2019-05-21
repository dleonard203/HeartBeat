from sql_schemas import *
from flask import Flask, render_template, request, session, redirect
import time
import sqlite3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker





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
    print(f"res: {res}")
    if res == None:
        return False
    return True

def create_account(username, password, email):
    u = Users(username=username, password=password, email=email)
    db.add(u)
    db.commit()



