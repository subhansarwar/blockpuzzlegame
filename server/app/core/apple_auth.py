# app/core/apple_auth.py
import json

import httpx
import jwt as pyjwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, status

from app.core.config import settings

_APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
_APPLE_ISSUER = "https://appleid.apple.com"


async def verify_apple_token(identity_token: str) -> dict:
    """
    Verify an Apple identity token (JWT) server-side.

    Steps:
      1. Decode the JWT header to find which Apple public key was used (kid).
      2. Fetch Apple's current public keys from their JWKS endpoint.
      3. Verify the JWT signature, audience, and issuer.
      4. Return the verified claims: sub (stable user ID) and email.
    """
    if not settings.APPLE_CLIENT_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Apple Sign-In is not configured")

    try:
        header = pyjwt.get_unverified_header(identity_token)
    except pyjwt.DecodeError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Malformed Apple token: {exc}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(_APPLE_KEYS_URL)
            resp.raise_for_status()
            jwks = resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Could not fetch Apple keys: {exc}")

    key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")), None)
    if not key_data:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Apple public key not found for this token")

    public_key = RSAAlgorithm.from_jwk(json.dumps(key_data))

    try:
        payload = pyjwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID,
            issuer=_APPLE_ISSUER,
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Apple token has expired")
    except pyjwt.InvalidAudienceError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Apple token audience mismatch")
    except pyjwt.InvalidIssuerError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Apple token issuer mismatch")
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Apple token: {exc}")

    sub = payload.get("sub")
    email = payload.get("email")

    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Apple token missing 'sub' claim")

    return {"sub": sub, "email": email}
