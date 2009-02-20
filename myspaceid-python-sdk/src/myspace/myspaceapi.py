#!/usr/bin/python
#
# Copyright (C) 2007, 2008 MySpace Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'cnanga@myspace.com (Chak Nanga)'

import httplib
import sys
import urllib2
import exceptions
import simplejson
from oauthlib import oauth

__all__ = [
    'MySpace',
    'MySpaceError',
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
    def __init__(self, message, http_response=None):
        Exception.__init__(self, message)
        self.http_response = http_response
    
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
        self.__validate_params(locals())
        albums_request_url = API_ALBUMS_URL % user_id
        #set up extra params, if any
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size
        return self.__call_myspace_api(albums_request_url, parameters=params)
    
    def get_album(self, user_id, album_id):
        self.__validate_params(locals())
        album_request_url = API_ALBUM_URL % (user_id, album_id)
        return self.__call_myspace_api(album_request_url)
    
    def get_friends(self, user_id, page=None, page_size=None, list=None, show=None):
        self.__validate_params(locals())
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
        self.__validate_params(locals())
        friendship_request_url = API_FRIENDSHIP_URL % (user_id, friend_ids)
        return self.__call_myspace_api(friendship_request_url)

    def get_mood(self, user_id):
        self.__validate_params(locals())
        mood_request_url = API_MOOD_URL % user_id
        return self.__call_myspace_api(mood_request_url)

    def get_photos(self, user_id, page=None, page_size=None):
        self.__validate_params(locals())
        photos_request_url = API_PHOTOS_URL % user_id       
        #set up extra params, if any
        params = {}
        if page is not None:
            params['page'] = page
        if page_size is not None:
            params['page_size'] = page_size            
        return self.__call_myspace_api(photos_request_url, parameters=params)

    def get_photo(self, user_id, photo_id):
        self.__validate_params(locals())
        photo_request_url = API_PHOTO_URL % (user_id, photo_id)
        return self.__call_myspace_api(photo_request_url)
    
    def get_profile(self, user_id):        
        self.__validate_params(locals())
        profile_request_url = API_PROFILE_URL % user_id
        return self.__call_myspace_api(profile_request_url)

    def get_status(self, user_id):
        self.__validate_params(locals())
        status_request_url = API_STATUS_URL % user_id
        return self.__call_myspace_api(status_request_url)

    def get_videos(self, user_id):
        self.__validate_params(locals())
        videos_request_url = API_VIDEOS_URL % user_id
        return self.__call_myspace_api(videos_request_url)

    def get_video(self, user_id, video_id):
        self.__validate_params(locals())
        video_request_url = API_VIDEO_URL % (user_id, video_id)
        return self.__call_myspace_api(video_request_url)
    
    """Miscellaneous utility functions 
    """
    def __validate_params(self, params):
        invalid_param = 'Invalid Parameter Value. %s %s'
        # Non empty/None param check
        non_empty_params = ['user_id']
        for param, value in params.items():
            if param in non_empty_params:
                if value is None or len(value) == 0:
                    message =  invalid_param % (param, ' cannot be None or empty')
                    raise MySpaceError(message)
                    return
        #Non-negative param check
        positive_params = ['page', 'page_size', 'user_id', 'video_id', 'photo_id', 'album_id']
        for param, value in params.items():
            if param in positive_params and value is not None:
                if value < 0:
                    message = invalid_param % (param, ' cannot be negative')
                    raise MySpaceError(message)
                    return
        
    def __call_oauth_api(self, oauth_url, token=None, debug=False):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=token, http_url=oauth_url
        )
        oauth_request.sign_request(self.signature_method, self.consumer, token)
        resp = self.url_fetcher.fetch(oauth_request.to_url())
        if resp.status is not 200:
            raise MySpaceError('MySpace OAuth API returned an error', resp)
        return resp.body 
      
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
        resp = self.url_fetcher.fetch(oauth_request.to_url())
        if resp.status is not 200:
            raise MySpaceError('MySpace REST API returned an error', resp)
        api_response = simplejson.loads(resp.body)        
        return api_response

class UrlFetcher(object):
      def fetch(self, url, body=None, headers=None):
        if headers is None:
           headers = {}
        req = urllib2.Request(url, data=body, headers=headers)
        try:
            f = urllib2.urlopen(req)
            try:
                return self._makeResponse(f)
            finally:
                f.close()
        except urllib2.HTTPError, why:
            try:
                return self._makeResponse(why)
            finally:
                why.close()

      def _makeResponse(self, urllib2_response):
        resp = HTTPResponse()
        resp.body = urllib2_response.read()
        resp.final_url = urllib2_response.geturl()
        resp.headers = dict(urllib2_response.info().items())
    
        if hasattr(urllib2_response, 'code'):
            resp.status = urllib2_response.code
        else:
            resp.status = 200   
        return resp

class HTTPResponse(object):
      headers = None
      status = None
      body = None
      final_url = None
    
      def __init__(self, final_url=None, status=None, headers=None, body=None):
          self.final_url = final_url
          self.status = status
          self.headers = headers
          self.body = body
    
      def __repr__(self):
          return "[HTTP Status Code: %r --- Request URL: %s --- Response: %s" % (self.status, self.final_url, self.body)
