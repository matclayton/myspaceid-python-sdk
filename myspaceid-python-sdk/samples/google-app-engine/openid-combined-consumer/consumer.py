#!/usr/bin/python
#
# Copyright 2008 Google Inc.
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

"""
A sample OpenID consumer app for Google App Engine. Allows users to log into
other OpenID providers, then displays their OpenID login. Also stores and
displays the most recent logins.

Part of http://code.google.com/p/google-app-engine-samples/.

For more about OpenID, see:
  http://openid.net/
  http://openid.net/about.bml

Uses JanRain's Python OpenID library, version 2.1.1, licensed under the
Apache Software License 2.0:
  http://openidenabled.com/python-openid/

The JanRain library includes a reference OpenID provider that can be used to
test this consumer. After starting the dev_appserver with this app, unpack the
JanRain library and run these commands from its root directory:

  setenv PYTHONPATH .
  python ./examples/server.py -s localhost

Then go to http://localhost:8080/ in your browser, type in
http://localhost:8000/test as your OpenID identifier, and click Verify.
"""

import datetime
import logging
import os
import re
import sys
import urlparse
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

from openid import fetchers
from openid.consumer.consumer import Consumer
from openid.consumer import discover
from openid.extensions import oauth
from myspace.myspaceapi import MySpace

import fetcher
import store
import gmemsess

# Set to True if stack traces should be shown in the browser, etc.
_DEBUG = False

class Login(db.Model):
  """A completed OpenID login."""
  status = db.StringProperty(choices=('success', 'cancel', 'failure'))
  claimed_id = db.LinkProperty()
  server_url = db.LinkProperty()
  timestamp = db.DateTimeProperty(auto_now_add=True)

class Handler(webapp.RequestHandler):
  """A base handler class with a couple OpenID-specific utilities."""
  consumer = None
  session = None

  def __init__(self):
    self.session = {}

  def get_consumer(self):
    """Returns a Consumer instance.
    """
    if not self.consumer:
      fetchers.setDefaultFetcher(fetcher.UrlfetchFetcher())
      self.consumer = Consumer(self.session, store.DatastoreStore())

    return self.consumer

  def args_to_dict(self):
    """Converts the URL and POST parameters to a singly-valued dictionary.

    Returns:
      dict with the URL and POST body parameters
    """
    req = self.request
    return dict([(arg, req.get(arg)) for arg in req.arguments()])

  def render(self, extra_values={}):
    """Renders the page, including the extra (optional) values.

    Args:
      template_name: string
      The template to render.

      extra_values: dict
      Template values to provide to the template.
    """
    values = {}
    values.update(extra_values)
    cwd = os.path.dirname(__file__)
    path = os.path.join(cwd, 'templates', 'base.html')
    self.response.out.write(template.render(path, values, debug=_DEBUG))

  def report_error(self, message, exception=None):
    """Shows an error HTML page.

    Args:
      message: string
      A detailed error message.
    """
    if exception:
      logging.exception('Error: %s' % message)
    self.render({'error': message})

  def show_front_page(self):
    """Do an internal (non-302) redirect to the front page.

    Preserves the user agent's requested URL.
    """
    front_page = FrontPage()
    front_page.request = self.request
    front_page.response = self.response
    front_page.get()


class FrontPage(Handler):
  """Show the default front page."""
  def get(self):
    self.render()


class LoginHandler(Handler):
  """Handles a POST response to the OpenID login form."""

  def post(self):
    """Handles login requests."""

    # Start a new session for the in progress login as required by the OpenID Consumer class
    self.session = gmemsess.Session(self)

    logging.info(self.args_to_dict())
    openid_url = self.request.get('openid')
    if not openid_url:
      self.report_error('Please enter an OpenID URL.')
      return
   
    logging.debug('Beginning discovery for OpenID %s' % openid_url)
    try:
      consumer = self.get_consumer()
      if not consumer:
        return
      auth_request = consumer.begin(openid_url)
    except discover.DiscoveryFailure, e:
      self.report_error('Error during OpenID provider discovery.', e)
      return
    except discover.XRDSError, e:
      self.report_error('Error parsing XRDS from provider.', e)
      return

    # Note that at this stage self.session will have all of the discovered info
    # we want to save betweeen requests - the library adds that info to the session object
    # we supply it
    # We can also add our own info. as shown below to the session object as shown below
    self.session['claimed_id'] = auth_request.endpoint.claimed_id
    self.session['server_url'] = auth_request.endpoint.server_url
    self.session.save()

    # Also try to get authorization to access the user's Contact data (via the oAuth extension)
    consumer_key = MySpace.CONSUMER_KEY
    scope = None
    oauth_authorize_request = oauth.OauthAuthorizeTokenRequest(consumer_key, scope)
    auth_request.addExtension(oauth_authorize_request)
    
    parts = list(urlparse.urlparse(self.request.uri))
    parts[2] = 'finish'
    return_to = urlparse.urlunparse(parts)
    realm = urlparse.urlunparse(parts[0:2] + [''] * 4)
    
    redirect_url = auth_request.redirectURL(realm, return_to)
    logging.debug('Redirecting to %s' % redirect_url)
    self.response.set_status(302)
    self.response.headers['Location'] = redirect_url


class FinishHandler(Handler):
  """Handle a redirect from the provider."""
  def get(self):
    # Try to get the previously stored session data  
    self.session = gmemsess.Session(self)
    
    args = self.args_to_dict()
    consumer = self.get_consumer()
    if not consumer:
      return

    response = consumer.complete(args, self.request.uri)

    if response.status == 'success':
      """
      sreg_data = sreg.SRegResponse.fromSuccessResponse(response).items()
      ax_data = ax.FetchResponse.fromSuccessResponse(response)
      """
      oauth_data = oauth.OauthAuthorizeTokenResponse.fromSuccessResponse(response)
      if (oauth_data.authorized_request_token):
          ms = MySpace()
          oauth_access_token = ms.get_access_token(oauth_data.authorized_request_token)
          user_data = ms.get_userinfo(oauth_access_token)
          userId = user_data['userId']
          profile_data = ms.get_profile(userId, oauth_access_token)
          friends_data = ms.get_friends(userId, oauth_access_token)
          albums_data = ms.get_albums(userId, oauth_access_token)
      else:
          profile_data = friends_data = None
    elif response.status == 'failure':
      logging.error(str(response))

    logging.debug('Login status %s for claimed_id %s' %
                  (response.status, response.endpoint.claimed_id))

    login = Login(status=response.status,
                  claimed_id=response.endpoint.claimed_id,
                  server_url=response.endpoint.server_url)
    login.put()

    # Get rid of the session data
    self.session.invalidate()
    
    self.render(locals())


# Map URLs to our RequestHandler subclasses above
_URLS = [
  ('/', FrontPage),
  ('/login', LoginHandler),
  ('/finish', FinishHandler),
]

def main(argv):
  logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication(_URLS, debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main(sys.argv)
