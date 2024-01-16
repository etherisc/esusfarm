from configparser import ConfigParser
from fastapi import HTTPException, FastAPI
from fastapi.routing import APIRouter
from loguru import logger
from loguru._logger import Logger
from nanoid import generate

from server.config import Settings
from server.error import raise_with_log
from util.logging import get_logger

import functools
import jwt
import os
import sys

NANO_ID_SIZE=12

logger = get_logger()

def create_app(settings: Settings) -> FastAPI:
    return FastAPI(
        title=settings.APP_TITLE,
        debug=settings.APP_DEBUG)


def include_router(app: FastAPI, router: APIRouter, message: str) -> None:
    logger.info(message)
    app.include_router(router)


def setup_logging(settings: Settings) -> Logger:
    logger.remove()
    logger.add(
        sys.stdout, 
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL, 
        colorize=settings.LOG_COLORIZE)

    return logger


def getenv_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, default)
    
    if isinstance(value, bool):
        return value
    
    return value.lower() in ["true", "1"]


def getenv_int(name: str, default: int = 0) -> int:
    value = os.getenv(name, default)
    
    if isinstance(value, int):
        return value
    
    return int(value)


def verify_jwt(func):
    """Sleep 1 second before calling the function"""
    @functools.wraps(func)
    def wrapper_verify_jwt(*args, **kwargs):
        token = kwargs['token']
        jwt_verify_result = VerifyToken(token.credentials).verify()
        if jwt_verify_result.get("status"):
            print("JWT invalid")
            logger.warning("Unauthorized")
            raise HTTPException(status_code=401, detail="Unauthorized")
        return func(*args, **kwargs)
    return wrapper_verify_jwt


def set_up():
    """Sets up configuration for the app"""

    env = os.getenv("ENV", ".config")

    if env == ".config":
        config = ConfigParser()
        config.read(".config")
        config = config["AUTH0"]
    else:
        config = {
            "DOMAIN": os.getenv("DOMAIN", "your.domain.com"),
            "API_AUDIENCE": os.getenv("API_AUDIENCE", "your.audience.com"),
            "ISSUER": os.getenv("ISSUER", "https://your.domain.com/"),
            "ALGORITHMS": os.getenv("ALGORITHMS", "RS256"),
        }
    return config


class VerifyToken():
    """Does all the token verification using PyJWT"""

    def __init__(self, token):
        self.token = token
        self.config = set_up()

        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f'https://{self.config["DOMAIN"]}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    def verify(self):
        # This gets the 'kid' from the passed token
        try:
            self.signing_key = self.jwks_client.get_signing_key_from_jwt(
                self.token
            ).key
        except jwt.exceptions.PyJWKClientError as error:
            return {"status": "error", "msg": error.__str__()}
        except jwt.exceptions.DecodeError as error:
            return {"status": "error", "msg": error.__str__()}

        try:
            payload = jwt.decode(
                self.token,
                self.signing_key,
                algorithms=self.config["ALGORITHMS"],
                audience=self.config["API_AUDIENCE"],
                issuer=self.config["ISSUER"],
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}

        print("JWT payload: %s" % payload)
        return payload
    