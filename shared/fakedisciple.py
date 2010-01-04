#!/usr/bin/python

# fakedisciple is a disciple simulator. Gives you access to unix 'touch' and
# 'rm' commands to send/remove signals.
#
# How to use:
#   Place in cgi-bin folder of your web server and give it executable rights.


from libwebapp import *
import cgi
import cgitb
import subprocess

###############
# neccessary for CGI to work
print "Content-Type: text/html"
print
###############

print "<h1>Disciple Simulator!</h1>"

print """
    <h2>Toucher</h2>
    <form name="toucher" method="post" action="fakedisciple.py">
    <input type="text" name="touch" value="signal_id">
    <input type="submit" value="Touch!"><br>
    <input type="text" name="touch"><br>
    </form>

    <h2>Remover</h2>
    <form name="remover" method="post" action="fakedisciple.py">
    <input type="text" name="rm" value="signal_id">
    <input type="submit" value="Remove!"><br>
    <input type="text" name="rm"><br>
    </form>
"""

form = cgi.FieldStorage()
if form.has_key("touch"):
    for id in form.getlist("touch"):
        subprocess.call(["touch", "signals/"+id])
        print "<p>"
        print "<b>Message: </b>" + id + " touched."
        print "</p>"

if form.has_key("rm"):
    for id in form.getlist("rm"):
        subprocess.call(["rm", "signals/"+id])
        print "<p>"
        print "<b>Message: </b>" + id + " removed."
        print "</p>"

print "<h2>signals directory:</h2>"
for s in sorted(os.listdir("signals")):
    print s + "<br>"


