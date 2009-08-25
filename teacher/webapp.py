#!/usr/bin/python
# Maintained by Elben Shira @ gmail.

from libwebapp import *
import cgi
import cgitb

##############
# Teacher Control Setup
#
# Please set these variables!
##############
SIGNALS_DIR = "/var/www"    # path to signals directory
REFRESH_RATE = 3            # refresh every num of seconds
                            # if <= 0, then never refresh automatically
                            # NOTE: currently unimplemented.

##############
# No need to touch anything below
# unless you know what you are doing.
##############

cgitb.enable()
form = cgi.FieldStorage()
app = TeacherControl(dir=SIGNALS_DIR)

###############
# neccessary for CGI to work
print "Content-Type: text/html"
print
###############

###############
# Signal Logic
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

print """<h2><a href="javascript:location.reload(true)">Refresh!</a></h2>"""

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
      <form id="armcontrol" name="armcontrol" method="post"
      action="webapp.py">
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
    <form id="recordcontrol" name="recordcontrol" method="post"
    action="webapp.py">
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
    <form id="endrecordcontrol" name="endrecordcontrol" method="post"
    action="webapp.py">
"""

for id, state in zip(app.disciples, app.states):
    if app.record_verified(state):
        s = '<input type="checkbox" name="endrecord" value="'+id+'" />'+id+'<br>'
        print s
print """
    <input type="submit" value="Send End Record Signal">
    </form>
"""
