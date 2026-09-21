FROM python:3.12-slim

# The mint verifies real RS256 Actions OIDC tokens against the emulator's
# JWKS, so it needs a JWT implementation with cryptography available.
RUN pip install --no-cache-dir "pyjwt[crypto]==2.12.1"

COPY server.py /app/server.py
WORKDIR /app

EXPOSE 8080
ENTRYPOINT ["python", "/app/server.py"]
