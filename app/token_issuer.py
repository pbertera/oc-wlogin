#!/usr/bin/python

import ast
import json
import oauthlib.oauth2.rfc6749.errors as OauthErrors
import os
import sys
import urllib.parse
import web
from requests_oauthlib import OAuth2Session

web.config.debug = False

def bailout(error):
    print('ERROR: %s' % error)
    sys.exit(255)

# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

if 'OC_WLOGIN_CLIENT_ID' in os.environ:
    client_id = os.environ['OC_WLOGIN_CLIENT_ID']
else:
    bailout('OC_WLOGIN_CLIENT_ID not defined')

if 'OC_WLOGIN_CLIENT_SECRET' in os.environ:
    client_secret = os.environ['OC_WLOGIN_CLIENT_SECRET']
else:
    bailout('OC_WLOGIN_CLIENT_SECRET node defined')

if 'OC_WLOGIN_AUTH_URL' in os.environ:
    authorization_base_url = os.environ['OC_WLOGIN_AUTH_URL'] #'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/authorize'
else:
    bailout('OC_WLOGIN_AUTH_URL not defined')

if 'OC_WLOGIN_TOKEN_URL' in os.environ:
    token_url = os.environ['OC_WLOGIN_TOKEN_URL'] # 'https://oauth-openshift.apps.pberteramfa.lab.upshift.rdu2.redhat.com/oauth/token'
else:
    bailout('OC_WLOGIN_TOKEN_URL not defined')

if 'OC_WLOGIN_TLS_CERT' in os.environ:
    tls_cert = os.environ['OC_WLOGIN_TLS_CERT']
    if 'OC_WLOGIN_TLS_KEY' in os.environ:
        tls_key = os.environ['OC_WLOGIN_TLS_KEY']
    else:
        bailout('OC_WLOGIN_TLS_KEY not defined')
else:
    tls_cert = None
    #bailout('OC_WLOGIN_TLS_CERT not defined')

if 'OC_WLOGIN_CA_BUNDLE' in os.environ:
    ca_bundle = os.environ['OC_WLOGIN_CA_BUNDLE']
else:
    ca_bundle = False

if 'OC_WLOGIN_SESSIONS_DIR' in os.environ:
    sessions_dir = os.environ['OC_WLOGIN_SESSIONS_DIR']
else:
    sessions_dir = '/tmp/sessions'


if tls_cert:
    from cheroot.server import HTTPServer
    from cheroot.ssl.builtin import BuiltinSSLAdapter

    HTTPServer.ssl_adapter = BuiltinSSLAdapter(
            certificate=tls_cert,
            private_key=tls_key)

urls = (
    '/login/(.*)', 'Login',
    '/callback', 'Callback',
    '/token/(.*)', 'Token',
    '/healthz', 'Healthz'
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
        try:
            token = oauth_server.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=web.ctx.home + '/' + web.ctx.fullpath, verify=ca_bundle)
        except OauthErrors.UnauthorizedClientError as e:
            return render.error("Error retriving the token: %s" % e)
        token_json = json.dumps(ast.literal_eval("%s" % token))
        setattr(web.ctx.globals, state, token_json)
        session.kill()
        return render.callback(state)

class Token:
    def GET(self, state):
        params = web.input(display=False)
        try:
            token = getattr(web.ctx.globals, state)
            if token == '{}':
                raise web.notfound("Token Not Found")
        except AttributeError:
            raise web.notfound("Token Not Found")
        delattr(web.ctx.globals, state)
        if params.display:
            return render.token(token)
        else:
            return token

class Healthz:
    def GET(self):
        return "{'status':'ok'}"

if __name__ == "__main__":
    app.run()
