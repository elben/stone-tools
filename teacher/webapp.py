#!/usr/bin/python

from libwebapp import *
import cgi
import cgitb

cgitb.enable()
form = cgi.FieldStorage()
app = TeacherControl(dir="signals")

###############
# neccessary for CGI to work
print "Content-Type: text/html"
print
###############

# send 'arm' signals
if form.has_key("arm"):
    ids = []
    for id in form.getlist("arm"):
        ids.append(id)
    app.signal_arm(ids)

# send 'record' signals
if form.has_key("record"):
    ids = []
    for id in form.getlist("record"):
        ids.append(id)
    app.signal_record(ids)

# remove 'record' signals
if form.has_key("endrecord"):
    ids = []
    for id in form.getlist("endrecord"):
        ids.append(id)
    app.signal_end_record(ids)

################
# Intro
################
print "<h1>Stone Tools: webapp</h1>"
print "<hr>"

# receive 'exist' signals
app.verify_exist()
print "<h2>Status</h2>"
for id in app.disciples:
    print app.status_str(id)
    print "<br />"

################
# Arming station
################

print """
      <h2>Arm</h2>
      <form name="armcontrol" method="post" action="webapp.py">
      """

for id, state in zip(app.disciples, app.states):
    if not app.arm_verified(state) and app.exist_verified(state):
        s = '<input type="checkbox" name="arm" value="'+id+'" />'+id+'<br>'
        print s
print """
    <input type="submit" value="Send Arm Signal">
    </form>
"""

################
# Recording station
################
print """
    <h2>Record</h2>
    <form name="recordcontrol" method="post" action="webapp.py">
"""

for id, state in zip(app.disciples, app.states):
    if not app.record_verified(state) and app.arm_verified(state):
        s = '<input type="checkbox" name="record" value="'+id+'" />'+id+'<br>'
        print s
print """
    <input type="submit" value="Send Record Signal">
    </form>
"""

################
# End Recording station
################
print """
    <h2>End Recording</h2>
    <form name="endrecordcontrol" method="post" action="webapp.py">
"""

for id, state in zip(app.disciples, app.states):
    if app.record_verified(state):
        s = '<input type="checkbox" name="endrecord" value="'+id+'" />'+id+'<br>'
        print s
print """
    <input type="submit" value="Send End Record Signal">
    </form>
"""
