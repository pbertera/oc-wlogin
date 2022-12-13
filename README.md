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
