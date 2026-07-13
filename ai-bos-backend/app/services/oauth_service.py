from __future__ import annotations

import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings

SUPPORTED_PROVIDERS = ("google", "microsoft")

# In-memory OAuth state (single-process MVP).
_oauth_states: dict[str, dict[str, Any]] = {}


def _cleanup_states() -> None:
    now = time.time()
    expired = [k for k, v in _oauth_states.items() if v.get("exp", 0) < now]
    for key in expired:
        _oauth_states.pop(key, None)


def provider_config(provider: str) -> dict[str, Any]:
    provider = provider.lower()
    if provider == "google":
        client_id = settings.google_client_id
        client_secret = settings.google_client_secret
        authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
        token_url = "https://oauth2.googleapis.com/token"
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        scopes = "openid email profile"
    elif provider == "microsoft":
        client_id = settings.microsoft_client_id
        client_secret = settings.microsoft_client_secret
        authorize_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        userinfo_url = "https://graph.microsoft.com/v1.0/me"
        scopes = "openid email profile User.Read"
    else:
        raise ValueError(f"Provider non supporté: {provider}")

    live = bool(client_id and client_secret)
    return {
        "provider": provider,
        "client_id": client_id,
        "client_secret": client_secret,
        "authorize_url": authorize_url,
        "token_url": token_url,
        "userinfo_url": userinfo_url,
        "scopes": scopes,
        "enabled": True,
        "mode": "live" if live else "mock",
    }


def list_providers() -> list[dict[str, Any]]:
    return [
        {
            "id": p,
            "enabled": True,
            "mode": provider_config(p)["mode"],
        }
        for p in SUPPORTED_PROVIDERS
    ]


def create_oauth_state(provider: str, redirect_uri: str) -> str:
    _cleanup_states()
    state = secrets.token_urlsafe(24)
    _oauth_states[state] = {
        "provider": provider,
        "redirect_uri": redirect_uri,
        "exp": time.time() + 600,
    }
    return state


def pop_oauth_state(state: str) -> dict[str, Any] | None:
    _cleanup_states()
    return _oauth_states.pop(state, None)


def build_authorize_url(provider: str, redirect_uri: str) -> dict[str, Any]:
    cfg = provider_config(provider)
    state = create_oauth_state(provider, redirect_uri)
    if cfg["mode"] == "mock":
        # Frontend completes via mock-login using this state.
        return {
            "provider": provider,
            "mode": "mock",
            "state": state,
            "authorizationUrl": f"{settings.app_public_url}/login?oauth={provider}&state={state}&mode=mock",
        }

    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": cfg["scopes"],
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return {
        "provider": provider,
        "mode": "live",
        "state": state,
        "authorizationUrl": f"{cfg['authorize_url']}?{urlencode(params)}",
    }


def exchange_code_for_profile(provider: str, code: str, redirect_uri: str) -> dict[str, str]:
    cfg = provider_config(provider)
    if cfg["mode"] == "mock":
        raise RuntimeError("OAuth live non configuré — utiliser mock-login")

    with httpx.Client(timeout=20.0) as client:
        token_res = client.post(
            cfg["token_url"],
            data={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        token_res.raise_for_status()
        token_data = token_res.json()
        access_token = token_data["access_token"]

        if provider == "google":
            info = client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            info.raise_for_status()
            body = info.json()
            return {
                "subject": str(body.get("sub") or ""),
                "email": str(body.get("email") or "").lower(),
                "first_name": str(body.get("given_name") or "OAuth"),
                "last_name": str(body.get("family_name") or provider.title()),
            }

        # Microsoft Graph
        info = client.get(
            cfg["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info.raise_for_status()
        body = info.json()
        email = (body.get("mail") or body.get("userPrincipalName") or "").lower()
        name = str(body.get("displayName") or "OAuth User").split(" ", 1)
        return {
            "subject": str(body.get("id") or ""),
            "email": email,
            "first_name": name[0] or "OAuth",
            "last_name": name[1] if len(name) > 1 else "User",
        }


def mock_profile(provider: str, email: str) -> dict[str, str]:
    local = email.split("@", 1)[0]
    parts = local.replace(".", " ").split()
    return {
        "subject": f"mock-{provider}-{email}",
        "email": email.lower().strip(),
        "first_name": (parts[0] if parts else "OAuth").title(),
        "last_name": (parts[1] if len(parts) > 1 else provider.title()),
    }
