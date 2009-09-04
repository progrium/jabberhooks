#!/usr/bin/env python

import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.api import xmpp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import mail
import time, urllib, os

HOOKAH_URL = "http://hookah.webhooks.org"

def baseN(num,b,numerals="0123456789abcdefghijklmnopqrstuvwxyz"): 
    return ((num == 0) and  "0" ) or (baseN(num // b, b).lstrip("0") + numerals[num % b])

class MainHandler(webapp.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user:
            logout_url = users.create_logout_url("/")
            hooks = JabberHook.all().filter('user =', user)
        else:
            login_url = users.create_login_url('/')
        self.response.out.write(template.render('templates/main.html', locals()))
    
    def post(self):
        if self.request.POST.get('name', None):
            h = JabberHook.all().filter('name =', self.request.POST['name']).get()
            h.delete()
        else:
            h = JabberHook(hook_url=self.request.POST['url'])
            h.put()
        self.redirect('/')

class RouterHandler(webapp.RequestHandler):
    def post(self):
        name = self.request.POST['to'].split('@')[0]
        hook = JabberHook.all().filter('name =', name).get()
        params = dict(self.request.POST)
        params['_url'] = hook.hook_url
        del params['stanza']
        urlfetch.fetch(url=HOOKAH_URL, payload=urllib.urlencode(params), method='POST')
        self.response.out.write("ok")

class JabberHook(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    hook_url = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
    def __init__(self, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', baseN(abs(hash(time.time())), 36))
        super(JabberHook, self).__init__(*args, **kwargs)

def main():
    application = webapp.WSGIApplication([('/', MainHandler), ('/_ah/xmpp/message/chat/', RouterHandler),], debug=True)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
