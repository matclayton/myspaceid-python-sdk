import httplib
import sys
import urllib2
import exceptions
import simplejson
from oauthlib import oauth

__all__ = [
    'MySpace',
    ]

OAUTH_REQUEST_TOKEN_URL = 'http://api.myspace.com/request_token'
OAUTH_AUTHORIZATION_URL = 'http://api.myspace.com/authorize'
OAUTH_ACCESS_TOKEN_URL  = 'http://api.myspace.com/access_token'

API_USERINFO_URL   = 'http://api.myspace.com/v1/user.json'
API_ALBUMS_URL     = 'http://api.myspace.com/v1/users/%s/albums.json'
API_ALBUM_URL      = 'http://api.myspace.com/v1/users/%s/albums/%s/photos.json'
API_FRIENDS_URL    = 'http://api.myspace.com/v1/users/%s/friends.json'
API_FRIENDSHIP_URL = 'http://api.myspace.com/v1/users/%s/friends/%s.json'
API_MOOD_URL       = 'http://api.myspace.com/v1/users/%s/mood.json'
API_PHOTOS_URL     = 'http://api.myspace.com/v1/users/%s/photos.json'
API_PHOTO_URL      = 'http://api.myspace.com/v1/users/%s/photos/%s.json'
API_PROFILE_URL    = 'http://api.myspace.com/v1/users/%s/profile.json'
API_STATUS_URL     = 'http://api.myspace.com/v1/users/%s/status.json'
API_VIDEOS_URL     = 'http://api.myspace.com/v1/users/%s/videos.json'
API_VIDEO_URL      = 'http://api.myspace.com/v1/users/%s/videos/%s.json'

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
      self.url_fetcher = UrlFetcher()

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
    
    def get_album(self, user_id, album_id):
        album_request_url = API_ALBUM_URL % (user_id, album_id)
        return self.__call_myspace_api(album_request_url)
    
    def get_friends(self, user_id, page=None, page_size=None, list=None, show=None):
        friends_request_url = API_FRIENDS_URL % user_id       
        #set up extra params, if any
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size
        if list is not None:
            params['list'] = list
        if show is not None:
            params['show'] = show             
        return self.__call_myspace_api(friends_request_url, parameters=params)

    def get_friendship(self, user_id, friend_ids):
        friendship_request_url = API_FRIENDSHIP_URL % (user_id, friend_ids)
        return self.__call_myspace_api(friendship_request_url)

    def get_mood(self, user_id):
        mood_request_url = API_MOOD_URL % user_id
        return self.__call_myspace_api(mood_request_url)

    def get_photos(self, user_id, page=None, page_size=None):
        photos_request_url = API_PHOTOS_URL % user_id       
        #set up extra params, if any
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size            
        return self.__call_myspace_api(photos_request_url, parameters=params)

    def get_photo(self, user_id, photo_id):
        photo_request_url = API_PHOTO_URL % (user_id, photo_id)
        return self.__call_myspace_api(photo_request_url)
    
    def get_profile(self, user_id):        
        profile_request_url = API_PROFILE_URL % user_id
        return self.__call_myspace_api(profile_request_url)

    def get_status(self, user_id):
        status_request_url = API_STATUS_URL % user_id
        return self.__call_myspace_api(status_request_url)

    def get_videos(self, user_id):
        videos_request_url = API_VIDEOS_URL % user_id
        return self.__call_myspace_api(videos_request_url)

    def get_video(self, user_id, video_id):
        video_request_url = API_VIDEO_URL % (user_id, video_id)
        return self.__call_myspace_api(video_request_url)
    
    """Miscellaneous utility functions 
    """
    def __call_oauth_api(self, oauth_url, token=None, debug=False):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=token, http_url=oauth_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        resp = self.url_fetcher.fetch(oauth_request.to_url(), debug)
        return resp 
      
    def __call_myspace_api(self, api_url, parameters=None, debug=False):
        #Check to make sure the contructor was call called with the access_token
        #before making API calls
        if self.token is None:
            raise MySpaceError('This function requires a valid OAuth Token. Make sure the oauth_token_key and oauth_token_secret are specified in the MySpace constructor')
        
        access_token = self.token
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_url=api_url, parameters=parameters
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)
        json = self.url_fetcher.fetch(oauth_request.to_url(), debug)
        api_response = simplejson.loads(json)        
        return api_response

class UrlFetcher(object):
  def fetch(self, url, body=None, headers=None, debug=False):    
    req = urllib2.Request(url)
    try:
      f = urllib2.urlopen(req)
      response = f.read()
    except urllib2.URLError, e:
      response = None
    return response
