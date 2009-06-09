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
import string
import exceptions
import simplejson
import urlparse
import cgi
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
API_MOODS_URL      = 'http://api.myspace.com/v1/users/%s/moods.json'
API_PHOTOS_URL     = 'http://api.myspace.com/v1/users/%s/photos.json'
API_PHOTO_URL      = 'http://api.myspace.com/v1/users/%s/photos/%s.json'
API_PROFILE_URL    = 'http://api.myspace.com/v1/users/%s/profile.json'
API_STATUS_URL     = 'http://api.myspace.com/v1/users/%s/status.json'
API_VIDEOS_URL     = 'http://api.myspace.com/v1/users/%s/videos.json'
API_VIDEO_URL      = 'http://api.myspace.com/v1/users/%s/videos/%s.json'
API_ACTIVITIES_URL = "http://api.myspace.com/v1/users/%s/activities.atom"
API_FRIENDSACTIVITIES_URL = "http://api.myspace.com/v1/users/%s/friends/activities.atom"
API_UPDATE_STATUS_URL = "http://api.myspace.com/v1/users/%s/status";
API_UPDATE_MOOD_URL   = "http://api.myspace.com/v1/users/%s/mood";
API_CREATE_ALBUM_URL = 'http://api.myspace.com/v1/users/%s/albums.json'
API_INDICATORS_URL = 'http://api.myspace.com/v1/users/%s/indicators.json'
API_NOTIFICATIONS_URL = 'http://api.myspace.com/v1/applications/%s/notifications'

class MySpaceError(Exception):
    def __init__(self, message, http_response=None):
        Exception.__init__(self, message)
        self.http_response = http_response
    
class MySpace():

    """Constructor can be invoked with or without the oauth token key/secret.
    
       Invoke it without the token for:
          - the oauth request_token and access_token API calls
          - "onsite" application calls i.e. for opensocial apps that are hosted in an iframe
          
       Invoke it with the token for:
          - MySpace ID application calls
    """
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
        # validate common parameters
        self.__validate_params(locals())
        #validate the list param - it can be one of 'top', 'online' or 'app'
        valid_list_values = ['top', 'online', 'app']
        if list is not None:
            if list not in valid_list_values:
                raise MySpaceError('Invalid Parameter Value. list must be one of %s' % str(valid_list_values))
                return
        #validate show parameter. show can be a combination of 'mood', 'status', 'online' separated by '|'
        valid_show_values = ['mood', 'status', 'online']
        if show is not None:
            given_show = string.split(show, '|')
            for s in given_show:
                if s not in valid_show_values:
                    raise MySpaceError('Invalid Parameter Value. show must be a combination of %s' % str(valid_show_values))
                    return
        # Proceed to making the request
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

    def get_moods(self, user_id):
        self.__validate_params(locals())
        moods_request_url = API_MOODS_URL % user_id
        return self.__call_myspace_api(moods_request_url)

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
    
    def get_profile(self, user_id, type='full'):        
        self.__validate_params(locals())
        #validate the type param - it can be one of 'basic', 'full' or 'extended'
        valid_type_values = ['basic', 'full', 'extended']
        if type is not None:
            if type not in valid_type_values:
                raise MySpaceError('Invalid Parameter Value. list must be one of %s' % str(valid_list_values))
                return
     
        params = {}
        params['detailtype'] = type
        
        profile_request_url = API_PROFILE_URL % user_id
        return self.__call_myspace_api(profile_request_url, parameters=params)

    def get_profile_basic(self, user_id):
        return self.get_profile(user_id, type='basic')

    def get_profile_full(self, user_id):
        return self.get_profile(user_id, type='full')

    def get_profile_extended(self, user_id):
        return self.get_profile(user_id, type='extended')
    
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

    def get_activities_atom(self, user_id):
        self.__validate_params(locals())
        activities_request_url = API_ACTIVITIES_URL % user_id
        return self.__call_myspace_api(activities_request_url, get_raw_response=True)

    def get_friends_activities_atom(self, user_id):
        self.__validate_params(locals())
        activities_request_url = API_FRIENDSACTIVITIES_URL % user_id
        return self.__call_myspace_api(activities_request_url, get_raw_response=True)

    def set_status(self, user_id, status):
        self.__validate_params(locals())
        if len(status) == 0:
            raise MySpaceError('status must be set to a non-empty string')
            return
        params = {}
        params['status'] = status
        update_status_url = API_UPDATE_STATUS_URL % user_id
        # setting get_raw_status=True since the REST API does not return any data on success
        return self.__call_myspace_api(update_status_url, method='PUT', parameters=params, get_raw_response=True)

    def set_mood(self, user_id, mood):
        self.__validate_params(locals())
        params = {}
        params['mood'] = mood
        update_mood_url = API_UPDATE_MOOD_URL % user_id
        # setting get_raw_status=True since the REST API does not return any data on success
        return self.__call_myspace_api(update_mood_url, method='PUT', parameters=params, get_raw_response=True)

    def create_album(self, user_id, title, location=None, privacy='Everyone'):
        self.__validate_params(locals())
        #validate the privacy param - it can be one of 'Everyone', 'FriendsOnly' or 'Me'
        valid_privacy_values = ['Everyone', 'FriendsOnly', 'Me']
        if privacy is not None:
            if privacy not in valid_privacy_values:
                raise MySpaceError('Invalid Parameter Value. list must be one of %s' % str(valid_privacy_values))
                return
        album_create_url = API_CREATE_ALBUM_URL % user_id
        # set up album location, title etc.
        params = {}
        params['title'] = title
        if privacy is not None:
            params['privacy'] = privacy
        if location is not None:
            params['location'] = location
        return self.__call_myspace_api(album_create_url, method='POST', parameters=params)

    def get_indicators(self, user_id):
        self.__validate_params(locals())
        get_indicators_url = API_INDICATORS_URL % user_id
        return self.__call_myspace_api(get_indicators_url)

    """
        send_notification Usage:
        
        ms = MySpace(ckeynsecret.CONSUMER_KEY, ckeynsecret.CONSUMER_SECRET)
        notification_data = ms.send_notification(135455, "296768296", "Test Notification With A Button", 
                                                 btn0_label="Go To Canvas", btn0_surface="canvas",
                                                 btn1_label="Go To App Profile", btn1_surface="appProfile",
                                                 mediaitems="http://api.myspace.com/v1/users/296768296")  
    """
    def send_notification(self, app_id, recipients, content, btn0_label=None, btn0_surface=None, btn1_label=None, btn1_surface=None, mediaitems=None):
        self.__validate_params(locals())
        if len(recipients) == 0:
           raise MySpaceError('recipients must be set to a non-empty string')
           return
        if len(content) == 0:
           raise MySpaceError('content must be set to a non-empty string')
           return

        params = {}
        params['recipients'] = recipients

        templateParameters = '{"content":"' + content + '"'
        if btn0_label is not None:
          if len(btn0_label) != 0:
             templateParameters += ',"button0_label":"' + btn0_label + '"' + ',"button0_surface":"' + btn0_surface + '"'
        if btn1_label is not None:
          if len(btn1_label) != 0:
             templateParameters += ',"button1_label":"' + btn1_label + '"' + ',"button1_surface":"' + btn1_surface + '"'
        templateParameters += '}'
        params['templateParameters'] = templateParameters

        if mediaitems is not None:
          if len(mediaitems) != 0:
             params['mediaitems'] = '{"' + mediaitems + '"}'     
        
        send_notification_url = API_NOTIFICATIONS_URL % app_id
        return self.__call_myspace_api(send_notification_url, method='POST', parameters=params)      
    
    """Miscellaneous utility functions 
    """
    def __validate_params(self, params):
        invalid_param = 'Invalid Parameter Value. %s %s'
        # Non empty/None param check
        non_empty_params = ['user_id', 'app_id']
        for param, value in params.items():
            if param in non_empty_params:
                try:
                    user_id = int(value)
                except (ValueError, TypeError):
                    message =  invalid_param % (param, ' must be an integer')
                    raise MySpaceError(message)
                    return
        #Non-negative param check
        positive_params = ['page', 'page_size', 'user_id', 'video_id', 'photo_id', 'album_id', 'mood']
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
        if resp.status != 200:
            raise MySpaceError('MySpace OAuth API returned an error', resp)
        return resp.body 
      
    def __call_myspace_api(self, api_url, method='GET', parameters=None, debug=False, get_raw_response=False):      
        access_token = self.token
        
        # Use POST for PUT as well. Set up http_method correctly for base string generation + signing
        http_method = 'POST' if (method == 'POST' or method == 'PUT') else method
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer, token=access_token, http_method=http_method, http_url=api_url, parameters=parameters
        )
        oauth_request.sign_request(self.signature_method, self.consumer, access_token)

        headers = {}
        body = None
        if (method == 'PUT'):
            headers['X-HTTP-Method-Override'] = 'PUT'           
        # Generate POST/PUT body
        if (method == 'PUT' or method == 'POST'):
            body = '&'.join('%s=%s' % (oauth.escape(str(k)), oauth.escape(str(v))) for k, v in parameters.iteritems())           
            
        """Get the request URL. For GET it's oauth_request.to_url(). For POST/PUT the URL should have just the oauth
           related params in the query string. Any request specific params go into the POST body - this is due to the
           way MySpace implements it's oauth
        """       
        request_url = oauth_request.to_url()
        if (method == 'POST' or method == 'PUT'):
            qs = urlparse.urlparse(oauth_request.to_url())[4]
            qparams = oauth_request._split_url_string(qs)
            for k, v in parameters.iteritems(): # nuke all non-oauth params and build a query string with only oauth related params
                del qparams[k]
            qs = '&'.join('%s=%s' % (oauth.escape(str(k)), oauth.escape(str(v))) for k, v in qparams.iteritems())
            request_url = oauth_request.get_normalized_http_url() + '?' + qs
        resp = self.url_fetcher.fetch(request_url, body=body, headers=headers)
        if resp.status > 201:
            raise MySpaceError('MySpace REST API returned an error', resp)
        api_response = resp.body if get_raw_response else simplejson.loads(resp.body)        
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
