from google.appengine.api import urlfetch

import simplejson
import ckeynsecret
import oauthlib as oauth

__all__ = [
    'OAuthRequestHelper',
    'CONSUMER_KEY',
    'CONSUMER_SECRET',
    ]

OAUTH_ACCESS_TOKEN_URL = 'http://api.myspace.com/access_token'

"""Use the following URL to get the user's full name, email
   this will work only in the case the user selects the "Also share my first name, last name, and email adress with <APP>" checkbox
   in the openid screen. Also, please note the change to get_userinfo_v2() below, where in we have to pass in the params separately

   API_USERINFO_URL_V2 = 'http://api.myspace.com/v2/people/@me/@self'
"""

API_USERINFO_URL = 'http://api.myspace.com/v1/user.json'
API_PROFILE_URL = 'http://api.myspace.com/v1/users/%s/profile.json'
API_FRIENDS_URL = 'http://api.myspace.com/v1/users/%s/friends.json'
API_ALBUMS_URL = 'http://api.myspace.com/v1/users/%s/albums.json'

CONSUMER_KEY    = ckeynsecret.CONSUMER_KEY
CONSUMER_SECRET = ckeynsecret.CONSUMER_SECRET

consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()

class OAuthRequestHelper():
    
    @staticmethod
    def fetch_response(oauth_request, debug=False):
      url = oauth_request.to_url()
      rv = urlfetch.fetch(url)
      s = rv.content
      if debug:
        print 'requested url: %s' % url
        print 'server response: %s' % s
      return s

    @staticmethod    
    def exchange_request_token_for_access_token(request_token):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=request_token, http_url=OAUTH_ACCESS_TOKEN_URL
        )
        oauth_request.sign_request(signature_method, consumer, request_token)
        resp = OAuthRequestHelper.fetch_response(oauth_request)
        return oauth.OAuthToken.from_string(resp) 

    @staticmethod
    def get_userinfo(access_token):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=access_token, http_url=API_USERINFO_URL
        )
        oauth_request.sign_request(signature_method, consumer, access_token)
        json = OAuthRequestHelper.fetch_response(oauth_request)
        return simplejson.loads(json)

    """ To be used with API_USERINFO_URL_V2 """
    @staticmethod
    def get_userinfo_V2(access_token):
        url_params = {'format' : 'json', 'fields' : 'emails,name,familyName' }
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=access_token, http_url=API_USERINFO_URL, parameters = url_params
        )
        oauth_request.sign_request(signature_method, consumer, access_token)
        json = OAuthRequestHelper.fetch_response(oauth_request)
        return simplejson.loads(json)

    @staticmethod
    def get_profile(userId, access_token):        
        profile_request_url = API_PROFILE_URL % userId

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=access_token, http_url=profile_request_url
        )
        oauth_request.sign_request(signature_method, consumer, access_token)
        json = OAuthRequestHelper.fetch_response(oauth_request)
        return simplejson.loads(json)
    
    @staticmethod
    def get_friends(userId, access_token):
        friends_request_url = API_FRIENDS_URL % userId
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=access_token, http_url=friends_request_url
        )
        oauth_request.sign_request(signature_method, consumer, access_token)
        json = OAuthRequestHelper.fetch_response(oauth_request)
        return simplejson.loads(json)

    @staticmethod
    def get_albums(userId, access_token):
        friends_request_url = API_ALBUMS_URL % userId
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            consumer, token=access_token, http_url=friends_request_url
        )
        oauth_request.sign_request(signature_method, consumer, access_token)
        json = OAuthRequestHelper.fetch_response(oauth_request)
        return simplejson.loads(json)

