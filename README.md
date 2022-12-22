# OpenShift web login

`oc` plugin and a web application to login from the console using the web browser.

Logging into OpenShift using an external IDP that requires human interaction (Eg with MFA) makes the `oc login` procedure a bit tricky:
You have to login into the web console and then retrieve the access token, requiring another login.

This project is a PoC consisting of:

- an application, running on OpenShift, which is registered as an OAuth client
- an `oc` plugin implementing the `oc wlogin` command

### Token retrieve flow

1. When the user executes the `oc wlogin` command a request to the `/login/` URL is performed, the application returns the Authorization URL together with the randomly generated state code.
2. The `oc-wlogin` plugin asks the user to open the Authorization URL in order to authenticate, in the meantime starts polling the `/token/$state_code`
3. Once the user logs into OpenShift using the browser gets redirected to the app `/callback/` URL, sending the authorization code to the application
4. The `/callback` endpoint of the application exchanges the authorization code for access token
5. When the token is retrieved it is exposed on the `/token/$state_code` URL
6. The `oc-wlogin` plugin can download the token, after the download is removed from the app memory
7. The `oc-wlogin` plugin performs `oc login --token $token`

## Application environment variables

- `OC_WLOGIN_CLIENT_ID` the OAuth client ID
- `OC_WLOGIN_CLIENT_SECRET` the OAuth client Secret
- `OC_WLOGIN_AUTH_URL` the OAuth server Authorize URL
- `OC_WLOGIN_TOKEN_URL` the OAuth server Token URL
- `OC_WLOGIN_TLS_CERT` path to the TLS certificate used by the App
- `OC_WLOGIN_TLS_KEY` path to the TLS certificate key used by the App
- `OC_WLOGIN_CA_BUNDLE` the CA bunle to trusting the OAuth authorize and token URLs
- `OC_WLOGIN_SESSIONS_DIR` path where the web sessions should be saved
- `OAUTHLIB_INSECURE_TRANSPORT` if set do not verify the certificate of the OAuth authorize and token URLs

## Installation

1. Clone this git repo
2. Configure the helm templates with proper `Values`
3. Install the helm chart `helm install oc-wlogin helm/oc-wlogin/ --namespace oc-wlogin --create-namespace` (first configure the `values.yaml`
4. Download the `oc-wlogin` plugin from https://raw.githubusercontent.com/pbertera/oc-wlogin/main/oc-plugin/oc-wlogin , save it into the `PATH` and make it executable

Now you should have an `oc-wlogin` route created into the `oc-wlogin` namespace, you can test the app with the browser connecting to the route `/login/` URL.

### oc wlogin usage

The `oc-wlogin` plugin adds a new `wlogin` OpenShift CLI command:

```
$ oc wlogin --help
USAGE: /var/home/pietro/bin/oc-wlogin [options] <API_URL>

Available Options:

-t, --token-issuer='': Token Issuer application URL (required if TOKEN_ISSUER is not defined)
-t, --idp='': The identity provider to be used (optional)
-c, --curl-opts='': curl(1) options to use when invoking the executable, default is '-s'
-p, --poll-time='': Defines the maximum token poll time in seconds (default 30)
```
