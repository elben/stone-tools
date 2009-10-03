#!/usr/bin/python
# Maintained by Elben Shira @ gmail.

from libwebapp import *

SIGNALS_DIR = "/var/www"

###############
# neccessary for CGI to work
print "Content-Type: text/html"
print
###############

app = TeacherControl(dir=SIGNALS_DIR)
print "<h2>Status</h2>"
for id in app.disciples:
    print app.status_str(id)
    print "<br />"
