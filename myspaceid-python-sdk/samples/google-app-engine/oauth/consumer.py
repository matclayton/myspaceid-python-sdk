import cgi
import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

import gmemsess
import ckeynsecret
from myspace.myspaceapi import MySpace
from oauthlib import oauth

"""
webapp handlers
1. / Index page, not logged in
   - Intro text plus link to auth with MySpace
2. /StartAuth Auth with MySpace
   - Creates an unauthed token, stashes in session, redirects user to MySpace
3. /OauthCallback Callback URL
   - Checks user's unauthed token session matches, if not shows error, otherwise
     exchanges for access token, stashes that in the session and redirects the
     user to /displayprofile page
4. /DisplayProfile
   - Looks up the user's profile and friends using their access token
"""
    
class IndexPage(webapp.RequestHandler):
    def get(self):
        session=gmemsess.Session(self)
        if 'access_token' in session:
            self.redirect('/displayprofile')
        else:
            path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
            self.response.out.write(template.render(path, {}))

class StartAuth(webapp.RequestHandler):
    def get(self):
        session=gmemsess.Session(self)    
        callback_url = self.request.host_url + '/callback'
        ms = MySpace(ckeynsecret.CONSUMER_KEY, ckeynsecret.CONSUMER_SECRET)
        request_token = ms.get_request_token()
        auth_url = ms.get_authorization_url(request_token, callback_url)
        session['unauthed_token'] = request_token.to_string()
        session.save()
        self.redirect(auth_url)

class OauthCallback(webapp.RequestHandler):
    def get(self):
        session=gmemsess.Session(self)
        str_unauthed_token = session['unauthed_token'] if 'unauthed_token' in session else None
        if not str_unauthed_token:
            self.response.out.write("No un-authed token found in session")
            return
        unauthorized_request_token = oauth.OAuthToken.from_string(str_unauthed_token)       
        if unauthorized_request_token.key != self.request.get('oauth_token', 'no-token'):
            self.response.out.write("Something went wrong! Tokens do not match")
            return
        ms = MySpace(ckeynsecret.CONSUMER_KEY, ckeynsecret.CONSUMER_SECRET)
        access_token = ms.get_access_token(unauthorized_request_token)
        session['access_token'] = access_token.to_string()
        session.save()
        self.redirect('/displayprofile')

class DisplayProfile(webapp.RequestHandler):
    def get(self):
        session=gmemsess.Session(self)
        str_access_token = session['access_token'] if 'access_token' in session else None
        if not str_access_token:
            self.response.out.write("You need an access token in the session!")
            return
        access_token = oauth.OAuthToken.from_string(str_access_token)    
        ms = MySpace(ckeynsecret.CONSUMER_KEY, ckeynsecret.CONSUMER_SECRET, access_token.key, access_token.secret)
        user_id = ms.get_userid()
        profile_data = ms.get_profile(user_id)
        friends_data = ms.get_friends(user_id)
        
        template_values = {
          'profile_data': profile_data,
          'friends_data': friends_data,
        }        
        path = os.path.join(os.path.dirname(__file__), 'templates/profile.html')
        self.response.out.write(template.render(path, template_values))
        session.invalidate()

application = webapp.WSGIApplication(
                                     [('/', IndexPage),
                                      ('/startauth', StartAuth),
                                      ('/callback', OauthCallback),
                                      ('/displayprofile', DisplayProfile)],
                                     debug=True)

def main():
  #logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
