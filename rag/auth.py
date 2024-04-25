import httpx
from datetime import datetime, timezone
import jwt
import time
from fastapi import HTTPException, Header, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
USER_POOL_ID = os.getenv("USER_POOL_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
COGNITO_ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}"
COGNITO_JWKS_URI = f"{COGNITO_ISSUER}/.well-known/jwks.json"


CACHE_TIME = 86400  # seconds

# Cache
jwks_cache = {"keys": None, "fetched_time": 0}

security = HTTPBearer()


async def fetch_cognito_keys():
    if jwks_cache["keys"] and (time.time() - jwks_cache["fetched_time"] < CACHE_TIME):
        return jwks_cache["keys"]
    async with httpx.AsyncClient() as client:
        response = await client.get(COGNITO_JWKS_URI)
        response.raise_for_status()
        jwks_cache["keys"] = {key["kid"]: key for key in response.json()["keys"]}
        jwks_cache["fetched_time"] = time.time()
    return jwks_cache["keys"]


async def decode_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    keys=Depends(fetch_cognito_keys),
):
    token = credentials.credentials
    
    try:
        unverified_headers = jwt.get_unverified_header(token)

        if unverified_headers["kid"] not in keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWK not found for given kid",
            )
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(
            keys[unverified_headers["kid"]]
        )
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=COGNITO_ISSUER,
        )

        # Additional payload validations
        current_time = datetime.now(timezone.utc).timestamp()
        if payload.get("exp") is None or current_time > payload["exp"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired, please re-login",
            )

        if payload.get("aud") != CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token: Incorrect audience",
            )

        if payload.get("iss") != COGNITO_ISSUER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token: Incorrect issuer",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired."
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error decoding token."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token provided."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
