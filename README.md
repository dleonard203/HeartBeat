# HeartBeat
A flask web app to help people with diabetes understand their blood sugar trends and other health-related data.
While this code is free to run in a local environment, it will also be hosted online (link coming soon).

# Motivation
There are a lot of apps out there for measuring diabetic related data. Heart rate monitors, blood sugar monitors,
general fitness apps. They tend to do a lot of things well, but not one thing perfect. Sometimes, a blood sugar
reading is very context specific, and some blood sugar monitors don't allow for context to be placed with the
number. Was your blood sugar high because you just ate? Was it high because you accidentally drank a non-diet soda? 
This important context gets lost. In some apps, the data collection is so intensive that it gets destroyed on weekly basis.

This app tries to simplify the understanding of diabetic related results. While there are no integrations with health
monitoring apps (yet), users are able to track their blood sugar (with notes), and get time-series representations of this
data. While hovering over charts, users get their notes on every data point, and get the relative rating of every
data point (low, normal, high) relative to context (pre-meal or post-meal).

The portal to enter data is simple (no one portal has more than 5 parts in a form), and users are able to update their
entries if they entered something incorrectly (or are given more context, such as the result of a phone call with a doctor
due to an irregularity).

# Features (to be continued)

# Setup (Tested on Ubuntu 16)
0.) Clone this code to a local filesystem or a server to run

1.) Open a terminal and change to the directory that you clonded this code to

2.) Create a new python3.6 virtual environment

3.) Run `pip3 install -r requirements.txt`

4.) Run `nohup flask_app.py >flask_app.log 2>&1 &` to set the server to run until error or process kill

5.) Connect to localhost:5000 in your favorite web browser (compatability tested in Chrome only) to start using!

