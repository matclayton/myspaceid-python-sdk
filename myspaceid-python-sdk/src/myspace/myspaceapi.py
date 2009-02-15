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

OAUTH_REQUEST_TOKEN_URL = 'http://api.myspace.com/request_token'
OAUTH_AUTHORIZATION_URL = 'http://api.myspace.com/authorize'
OAUTH_ACCESS_TOKEN_URL  = 'http://api.myspace.com/access_token'

API_USERINFO_URL = 'http://api.myspace.com/v1/user.json'
API_PROFILE_URL = 'http://api.myspace.com/v1/users/%s/profile.json'
API_FRIENDS_URL = 'http://api.myspace.com/v1/users/%s/friends.json'
API_ALBUMS_URL = 'http://api.myspace.com/v1/users/%s/albums.json'

def get_default_urlfetcher():
  if sys.modules.has_key('google.appengine.api.urlfetch'):
    return AppEngineUrlFetcher()
  return UrlFetcher()

class MySpaceError(Exception):
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
        resp = self.__call_oauth_api(OAUTH_REQUEST_TOKEN_URL)
        token = oauth.OAuthToken.from_string(resp)
        return token

    def get_authorization_url(self, token, callback_url):
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token, callback=callback_url, http_url=OAUTH_AUTHORIZATION_URL
        )
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        return oauth_request.to_url()

    def get_access_token(self, request_token):
        resp = self.__call_oauth_api(OAUTH_ACCESS_TOKEN_URL, token=request_token)
        token = oauth.OAuthToken.from_string(resp)
        return token

    """MySpace REST API wrapper functions 
    """  
    def get_userid(self):
        user_info = self.__call_myspace_api(API_USERINFO_URL)
        return user_info['userId']

    def get_albums(self, user_id, page=None, page_size=None):
        albums_request_url = API_ALBUMS_URL % user_id
        return self.__call_myspace_api(albums_request_url)
    
    def get_album(self, user_id, album_id=None):
        pass
    
    def get_friends(self, user_id, page=None, page_size=None, list=None, show=None):
        friends_request_url = API_FRIENDS_URL % user_id
        return self.__call_myspace_api(friends_request_url)

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
        return self.__call_myspace_api(profile_request_url)

    def get_status(self, user_id):
        pass

    def get_videos(self, user_id):
        pass

    def get_video(self, user_id, video_id):
        pass
    
    """Miscellaneous utility functions 
    """
    def __call_oauth_api(self, oauth_url, token=None, debug=False):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=token, http_url=oauth_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        resp = self.url_fetcher.fetch(oauth_request.to_url(), debug)
        return resp 
      
    def __call_myspace_api(self, api_url, debug=False):
        #Check to make sure the contructor was call called with the access_token
        #before making API calls
        if self.token is None:
            raise MySpaceError('This function requires a valid OAuth Token. Make sure the oauth_token_key and oauth_token_secret are specified in the MySpace constructor')
        
        access_token = self.token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=api_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.url_fetcher.fetch(oauth_request.to_url(), debug)
        api_response = simplejson.loads(json)        
        return api_response

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
