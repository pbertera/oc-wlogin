#!/usr/bin/python

# >>> client_id='openshift-browser-client'
#>>> scopes = []
#>>> auth_url = 'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/authorize'
#>>> from oauthlib.oauth2 import MobileApplicationClient
#>>> from requests_oauthlib import OAuth2Session
#>>> oauth = OAuth2Session(client=MobileApplicationClient(client_id=client_id), scope=scopes)
#>>> authorization_url, state = oauth.authorization_url(auth_url)
#>>> print(authorization_url)
# https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/authorize?response_type=token&client_id=openshift-browser-client&state=AFGgTNC8Hwh9iQwzObqhObHMifnApR

#kind: OAuthClient
#apiVersion: oauth.openshift.io/v1
#metadata:
# name: demo 
#secret: "123abc" 
#redirectURIs:
# - "http://127.0.0.1:8080/token" 
#grantMethod: auto


import web
import urllib.parse
import json
import ast
from requests_oauthlib import OAuth2Session

web.config.debug = False

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

client_id = "demo"
client_secret = "123abc"
authorization_base_url = 'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/authorize'
token_url = 'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/token'

urls = (
    '/login/(.*)', 'Login',
    '/callback', 'Callback',
    '/token/(.*)', 'Token'
)

def add_global_hook():
    g = web.storage({})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

app = web.application(urls, globals())
app.add_processor(add_global_hook())
session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'oauth_state': ''})

class Login:
    def GET(self, consumer=None):
        session.oauth_state = ''
        oauth_server = OAuth2Session(client_id)
        authorization_url, state = oauth_server.authorization_url(authorization_base_url)
        setattr(web.ctx.globals, state, '{}')
        if consumer == 'cli':
            return json.dumps({ 'authorization_url': authorization_url, 'state': state })
        session.oauth_state = state
        raise web.seeother(authorization_url)

class Callback:
    def GET(self):
        state = session.get('oauth_state')
        if state == '':
            data = web.input()
            state = data.state
        oauth_server = OAuth2Session(client_id, state=state)
        token = oauth_server.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=web.ctx.home + '/' + web.ctx.fullpath, verify=False) #FIXME
        token_json = json.dumps(ast.literal_eval("%s" % token))
        setattr(web.ctx.globals, state, token_json)
        session.kill()
        return(token_json)

class Token:
    def GET(self, state):
        try:
            token = getattr(web.ctx.globals, state)
            if token == '{}':
                raise web.notfound("Token Not Found")
        except AttributeError:
            raise web.notfound("Token Not Found")
        delattr(web.ctx.globals, state)
        return token

if __name__ == "__main__":
    app.run()
