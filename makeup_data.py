from flask_app import *
import datetime
import random

cur = datetime.datetime.now()
with app.app_context():
    for data_point in range(50):
        the_date = cur - datetime.timedelta(days=1)
        cur = the_date
        d = Daily(user_id=1, timestamp=str(the_date)[:19], weight=(190 + random.randint(-20, 20)), calories=random.randint(170, 220), steps=(5000 + random.randint(-2000, 5000)))
        db.add(d)


        h = Hourly(user_id=1, timestamp=str(the_date)[:19], blood_sugar=random.randint(56, 170), symptoms="Not feeling well", meal_status=random.randint(0, 1))
        db.add(h)
        db.commit()


