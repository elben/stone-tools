#!/usr/bin/python

from libwebapp import *
import cgi
import cgitb

cgitb.enable()
app = TeacherControl(dir=".")
form = cgi.FieldStorage()

###############
# neccessary for CGI to work
print "Content-Type: text/html"
print
###############

if form.has_key("arm"):
    print form["arm"]

print "<h1>Stone Tools: webapp</h1>"

app.verify_exist()
print """
    <h2>Arm Disciples</h2>
    <form name="teachercontrol" method="post" action="webapp.py">
"""

if len(app.disciples) == 0:
    print "No disciples exist!<br>"
for id in app.disciples:
    s = '<input type="checkbox" name="arm" value="'+id+'" />'+id+'<br>'
    print s
print """
    <input type="submit" value="Arm">
    </form>
"""

print "<h2>Status</h2>"
for id in app.disciples:
    print app.status_str(id)
    print "<br />"

