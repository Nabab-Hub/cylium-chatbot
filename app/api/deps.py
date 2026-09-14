import logging
from typing import Optional, Dict, Any
from fastapi import Header, Request, HTTPException
from firebase_admin import auth, firestore

from app.services.firebase import get_firestore_client
from app.utils.helpers import current_timestamp_ms, hash_api_key

logger = logging.getLogger("chatbot.deps")
SERVICE_ID = "chatbot"


async def get_current_user_id(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[str]:
    """
    Extracts user ID with entitlement validation:
    1. If X-API-Key is provided, validates key and active subscription to `chatbot`.
    2. If Bearer Firebase ID token is provided, validates user ID.
    3. Direct X-User-Id header.
    4. Returns None if unauthenticated guest.
    """
    # 1. API Key Auth
    if x_api_key and x_api_key.strip():
        db = get_firestore_client()
        clean_key = x_api_key.strip()
        key_hash = hash_api_key(clean_key)

        if db:
            query = (
                db.collection("apiKeys")
                .where(filter=firestore.FieldFilter("keyHash", "==", key_hash))
                .limit(1)
                .stream()
            )
            docs = list(query)
            if not docs:
                fallback_snap = db.collection("apiKeys").document(key_hash).get()
                if fallback_snap.exists:
                    key_data = fallback_snap.to_dict() or {}
                else:
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "success": False,
                            "error": "invalid_api_key",
                            "message": "Invalid API key",
                        },
                    )
            else:
                key_data = docs[0].to_dict() or {}

            # Status validation
            if key_data.get("status", "active") != "active":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "success": False,
                        "error": "api_key_inactive",
                        "message": "API key is inactive or revoked",
                    },
                )

            # Expiration
            expires_at = key_data.get("expiresAt")
            if expires_at:
                try:
                    exp_ms = int(expires_at.timestamp() * 1000) if hasattr(expires_at, "timestamp") else int(expires_at)
                    if exp_ms <= current_timestamp_ms():
                        raise HTTPException(
                            status_code=403,
                            detail={"success": False, "error": "api_key_expired", "message": "API key has expired"},
                        )
                except HTTPException:
                    raise
                except Exception:
                    pass

            # Subscription entitlement check for chatbot
            user_id = key_data.get("userId")
            if user_id:
                is_authorized = False
                # Admin check
                try:
                    user_snap = db.collection("users").document(user_id).get()
                    if user_snap.exists and (user_snap.to_dict() or {}).get("role") == "admin":
                        is_authorized = True
                except Exception:
                    pass

                # Override check
                if not is_authorized:
                    try:
                        override_snap = db.collection("userAccessOverrides").document(f"{user_id}_{SERVICE_ID}").get()
                        if override_snap.exists:
                            granted = (override_snap.to_dict() or {}).get("granted")
                            if granted is False:
                                # Check if user has an active subscription that supersedes this revocation
                                has_active_sub = False
                                try:
                                    now_ms = current_timestamp_ms()
                                    subs = (
                                        db.collection("subscriptions")
                                        .where(filter=firestore.FieldFilter("userId", "==", user_id))
                                        .where(filter=firestore.FieldFilter("status", "in", ["active", "pending"]))
                                        .stream()
                                    )
                                    for s in subs:
                                        sdata = s.to_dict() or {}
                                        if sdata.get("currentPeriodEnd", 0) > now_ms:
                                            sub_svc = sdata.get("serviceId", "")
                                            if sub_svc in [SERVICE_ID, "ai-chatbot", "all"]:
                                                has_active_sub = True
                                                break
                                            plan_id = sdata.get("planId")
                                            if plan_id:
                                                plan_doc = db.collection("plans").document(plan_id).get()
                                                if plan_doc.exists:
                                                    allowed = (plan_doc.to_dict() or {}).get("allowedServiceIds", [])
                                                    if "*" in allowed or "all" in allowed or SERVICE_ID in allowed:
                                                        has_active_sub = True
                                                        break
                                except Exception:
                                    pass

                                if has_active_sub:
                                    is_authorized = True
                                    try:
                                        override_snap.reference.delete()
                                    except Exception:
                                        pass
                                else:
                                    raise HTTPException(
                                        status_code=403,
                                        detail={
                                            "success": False,
                                            "error": "service_access_revoked",
                                            "message": f"Access to '{SERVICE_ID}' has been revoked by an administrator.",
                                        },
                                    )
                            if granted is True:
                                is_authorized = True
                    except HTTPException:
                        raise
                    except Exception:
                        pass

                # Active subscription check
                if not is_authorized:
                    try:
                        now_ms = current_timestamp_ms()
                        subs = (
                            db.collection("subscriptions")
                            .where(filter=firestore.FieldFilter("userId", "==", user_id))
                            .where(filter=firestore.FieldFilter("status", "in", ["active", "pending"]))
                            .stream()
                        )
                        for s in subs:
                            sdata = s.to_dict() or {}
                            if sdata.get("currentPeriodEnd", 0) > now_ms:
                                sub_svc = sdata.get("serviceId", "")
                                if sub_svc in [SERVICE_ID, "ai-chatbot", "all"]:
                                    is_authorized = True
                                    break
                                plan_id = sdata.get("planId")
                                if plan_id:
                                    plan_doc = db.collection("plans").document(plan_id).get()
                                    if plan_doc.exists:
                                        allowed = (plan_doc.to_dict() or {}).get("allowedServiceIds", [])
                                        if "*" in allowed or "all" in allowed or SERVICE_ID in allowed:
                                            is_authorized = True
                                            break
                    except Exception:
                        pass

                if not is_authorized:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "success": False,
                            "error": "service_not_subscribed",
                            "message": f"Access Denied: Your account does not have an active subscription for '{SERVICE_ID}'. Please subscribe to this service in your CyliumOS dashboard to unlock access.",
                        },
                    )

                return user_id

    # 2. Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token.get("uid")
            if uid:
                return uid
        except Exception as exc:
            logger.debug("Bearer token validation failed: %s", exc)

    # 3. Direct header
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()

    return None
