import httplib
import sys
import urllib2
try:
    from google.appengine.api import urlfetch
except:
    pass
import exceptions
import simplejson
from oauthlib import oauth

__all__ = [
    'MySpace',
    ]

REQUEST_TOKEN_URL = 'http://api.myspace.com/request_token'
AUTHORIZATION_URL = 'http://api.myspace.com/authorize'
ACCESS_TOKEN_URL  = 'http://api.myspace.com/access_token'

API_USERINFO_URL = 'http://api.myspace.com/v1/user.json'
API_PROFILE_URL = 'http://api.myspace.com/v1/users/%s/profile.json'
API_FRIENDS_URL = 'http://api.myspace.com/v1/users/%s/friends.json'
API_ALBUMS_URL = 'http://api.myspace.com/v1/users/%s/albums.json'

def get_default_urlfetcher():
  if sys.modules.has_key('google.appengine.api.urlfetch'):
    return AppEngineUrlFetcher()
  return UrlFetcher()

class ConfigurationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
    
class MySpace():

    def __init__(self, consumer_key, consumer_secret, oauth_token_key=None, oauth_token_secret=None):
      self.consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
      self.signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
      if oauth_token_key and oauth_token_secret:
          self.token = oauth.OAuthConsumer(oauth_token_key, oauth_token_secret)
      else:
          self.token = None          
      self.url_fetcher = get_default_urlfetcher()

    """OAuth Related functions 
    """  
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

    """MySpace REST API wrapper functions 
    """  
    def get_userid(self):
        """ TODO:---------MAKE SURE TO CHECK FOR TOKEN BEFORE MAKING THIS CALL
        """
        access_token = self.token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=API_USERINFO_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        user_info = simplejson.loads(json)
        return user_info['userId']

    def get_albums(self, user_id, page=None, page_size=None):
        albums_request_url = API_ALBUMS_URL % user_id
        access_token = self.token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=albums_request_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)
    
    def get_album(self, user_id, album_id=None):
        pass
    
    def get_friends(self, user_id, page=None, page_size=None, list=None, show=None):
        friends_request_url = API_FRIENDS_URL % user_id
        access_token = self.token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=friends_request_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)

    def get_friendship(self, user_id, friend_ids):
        pass

    def get_mood(self, user_id):
        pass

    def get_photos(self, user_id, page=None, page_size=None):
        pass

    def get_photo(self, user_id, photo_id):
        pass
    
    def get_profile(self, user_id):        
        profile_request_url = API_PROFILE_URL % user_id
        access_token = self.token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=profile_request_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.fetch_response(oauth_request)
        return simplejson.loads(json)

    def get_status(self, user_id):
        pass

    def get_videos(self, user_id):
        pass

    def get_video(self, user_id, video_id):
        pass
    
    """Miscellaneous utility functions 
    """  
    def fetch_response(self, oauth_request, debug=False):
      url = oauth_request.to_url()
      s = self.url_fetcher.fetch(url, debug)
      return s


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
