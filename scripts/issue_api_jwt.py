#!/usr/bin/env python3
"""Issue a long-lived Bearer JWT for API access (HS256)."""

import argparse
import secrets
import time

import jwt


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue eSusFarm API JWT")
    parser.add_argument("--secret", help="HS256 secret (default: random)")
    parser.add_argument("--years", type=int, default=10, help="Token validity in years")
    args = parser.parse_args()
    secret = args.secret or secrets.token_urlsafe(48)
    now = int(time.time())
    exp = now + args.years * 365 * 24 * 3600
    token = jwt.encode(
        {"sub": "esusfarm-api", "iat": now, "exp": exp},
        secret,
        algorithm="HS256",
    )
    print("API_JWT_SECRET=", secret, sep="")
    print("Bearer", token)


if __name__ == "__main__":
    main()