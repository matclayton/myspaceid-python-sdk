import httplib
import sys
import urllib2
try:
    from google.appengine.api import urlfetch
except:
    pass

import simplejson
import ckeynsecret
from oauthlib import oauth

__all__ = [
    'MySpace',
    ]

REQUEST_TOKEN_URL = 'http://api.myspace.com/request_token'
AUTHORIZATION_URL = 'http://api.myspace.com/authorize'
ACCESS_TOKEN_URL  = 'http://api.myspace.com/access_token'

"""Use the following URL to get the user's full name, email
   this will work only in the case the user selects the "Also share my first name, last name, and email adress with <APP>" checkbox
   in the openid screen. Also, please note the change to get_userinfo_v2() below, where in we have to pass in the params separately

   API_USERINFO_URL_V2 = 'http://api.myspace.com/v2/people/@me/@self'
"""

API_USERINFO_URL = 'http://api.myspace.com/v1/user.json'
API_PROFILE_URL = 'http://api.myspace.com/v1/users/%s/profile.json'
API_FRIENDS_URL = 'http://api.myspace.com/v1/users/%s/friends.json'
API_ALBUMS_URL = 'http://api.myspace.com/v1/users/%s/albums.json'

def get_default_urlfetcher():
  if sys.modules.has_key('google.appengine.api.urlfetch'):
    return AppEngineUrlFetcher()
  return UrlFetcher()

class MySpace():

    CONSUMER_KEY    = ckeynsecret.CONSUMER_KEY
    CONSUMER_SECRET = ckeynsecret.CONSUMER_SECRET
    
    def __init__(self):
      self.consumer = oauth.OAuthConsumer(MySpace.CONSUMER_KEY, MySpace.CONSUMER_SECRET)
      self.signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
      self.url_fetcher = get_default_urlfetcher()

    def fetch_response(self, oauth_request, debug=False):
      url = oauth_request.to_url()
      s = self.url_fetcher.fetch(url, debug)
      return s

    def get_request_token(self):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, http_url=REQUEST_TOKEN_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, None)
        resp = self.fetch_response(oauth_request)
        #logging.debug("Unauthorized Request Token = %s" % (resp))
        token = oauth.OAuthToken.from_string(resp)
        return token

    def get_authorization_url(self, token, callback_url):
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token, callback=callback_url, http_url=AUTHORIZATION_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        return oauth_request.to_url()

    def get_access_token(self, request_token):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=request_token, http_url=ACCESS_TOKEN_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, request_token)
        resp = self.fetch_response(oauth_request)
        return oauth.OAuthToken.from_string(resp) 

    def get_userinfo(self, access_token):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=API_USERINFO_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)

    """ To be used with API_USERINFO_URL_V2 """
    def get_userinfo_V2(self, access_token):
        url_params = {'format' : 'json', 'fields' : 'emails,name,familyName' }
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=API_USERINFO_URL, parameters = url_params
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)

    def get_profile(self, userId, access_token):        
        profile_request_url = API_PROFILE_URL % userId

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=profile_request_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)
    
    def get_friends(self, userId, access_token):
        friends_request_url = API_FRIENDS_URL % userId
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=friends_request_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)

    def get_albums(self, userId, access_token):
        friends_request_url = API_ALBUMS_URL % userId
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=friends_request_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)

class AppEngineUrlFetcher():
  """Implementation of UrlFetch using AppEngine's URLFetch API."""

  def fetch(self, url, debug=False):
      rv = urlfetch.fetch(url)
      s = rv.content
      if debug:
        print 'requested url: %s' % url
        print 'server response: %s' % s
      return s

class UrlFetcher():
  """Implementation of UrlFetch for non-AppEngine envs."""

  def fetch(self, url, debug=False):
      rv = urlfetch.fetch(url)
      s = rv.content
      if debug:
        print 'requested url: %s' % url
        print 'server response: %s' % s
      return s
