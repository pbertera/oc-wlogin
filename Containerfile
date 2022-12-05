FROM registry.access.redhat.com/ubi9/python-39
LABEL io.k8s.description="wlogin App requesting and exposing access token - Just a Proof of Concept" \
      io.k8s.display-name="wlogin App v0.0.1-PoC" \
      io.openshift.expose-services="8080:http"
RUN pip install web.py requests_oauthlib
COPY app/token_issuer.py /opt/
CMD ["python", "/opt/token_issuer.py"]
