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
import oauthlib.oauth2.rfc6749.errors as OauthErrors
from requests_oauthlib import OAuth2Session
import os

web.config.debug = False

# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# TODO: check envs
client_id = os.environ['OC_WLOGIN_CLIENT_ID']
client_secret = os.environ['OC_WLOGIN_CLIENT_SECRET']
authorization_base_url = os.environ['OC_WLOGIN_AUTH_URL'] #'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/authorize'
token_url = os.environ['OC_WLOGIN_TOKEN_URL'] # 'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/token'
tls_cert = os.environ['OC_WLOGIN_TLS_CERT']
tls_key = os.environ['OC_WLOGIN_TLS_KEY']
ca_bundle = os.environ['OC_WLOGIN_CA_BUNDLE']

if 'OC_WLOGIN_SESSIONS_DIR' in os.environ:
    sessions_dir = os.environ['OC_WLOGIN_SESSIONS_DIR']
else:
    sessions_dir = '/tmp/sessions'

from cheroot.server import HTTPServer
from cheroot.ssl.builtin import BuiltinSSLAdapter

HTTPServer.ssl_adapter = BuiltinSSLAdapter(
        certificate=tls_cert,
        private_key=tls_key)

urls = (
    '/login/(.*)', 'Login',
    '/callback', 'Callback',
    '/token/(.*)', 'Token',
    '//healthz', 'Healthz'
)

def add_global_hook():
    g = web.storage({})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

app = web.application(urls, globals())
app.add_processor(add_global_hook())
session = web.session.Session(app, web.session.DiskStore(sessions_dir), initializer={'oauth_state': ''})
render = web.template.render('templates/')

class Login:
    def GET(self, consumer=None):
        session.oauth_state = ''
        params = web.input(idp=None)
        oauth_server = OAuth2Session(client_id)
        authorization_url, state = oauth_server.authorization_url(authorization_base_url, idp=params.idp)
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
        if ca_bundle:
            verify = ca_bundle
        else:
            verify = false
        try:
            token = oauth_server.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=web.ctx.home + '/' + web.ctx.fullpath, verify=verify)
        except OauthErrors.UnauthorizedClientError as e:
            return render.error("Error retriving the token: %s" % e)
        token_json = json.dumps(ast.literal_eval("%s" % token))
        setattr(web.ctx.globals, state, token_json)
        session.kill()
        return render.callback(state)

class Token:
    def GET(self, state):
        try:
            token = getattr(web.ctx.globals, state)
            if token == '{}':
                raise web.notfound("Token Not Found")
        except AttributeError:
            raise web.notfound("Token Not Found")
        delattr(web.ctx.globals, state)
        return render.token(token)

class Healthz:
    def GET(self):
        return "{'status':'ok'}"

if __name__ == "__main__":
    app.run()
