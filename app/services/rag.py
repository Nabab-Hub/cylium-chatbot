import time
import logging
from typing import Optional, Dict, Any, List
from app.core.constants import CYLIUMOS_MASTER_KNOWLEDGE
from app.core.config import get_settings
from app.services import firebase as fb_service

logger = logging.getLogger("chatbot.rag")


class RAGContextService:
    """
    RAG (Retrieval Augmented Generation) Service for CyliumOS.
    Collects:
    1. Static domain knowledge (architecture, core models, policies, guides)
    2. Dynamic Firestore data (active registered services and subscription plans)
    3. Live User Account context (subscriptions, API keys, usage quotas)
    """

    def __init__(self):
        self._cached_services: List[Dict[str, Any]] = []
        self._cached_plans: List[Dict[str, Any]] = []
        self._last_catalog_fetch: float = 0.0

    def _refresh_catalog_cache_if_needed(self) -> None:
        """
        Refreshes the services and plans cache from Firestore if TTL expired.
        """
        now = time.time()
        ttl = get_settings().rag_cache_ttl_seconds
        if (now - self._last_catalog_fetch) < ttl and self._cached_services:
            return

        try:
            services = fb_service.fetch_active_services()
            plans = fb_service.fetch_active_plans()
            if services:
                self._cached_services = services
            if plans:
                self._cached_plans = plans
            self._last_catalog_fetch = now
            logger.debug(
                "Refreshed RAG catalog cache: %d services, %d plans.",
                len(self._cached_services),
                len(self._cached_plans),
            )
        except Exception as exc:
            logger.warning("Failed to refresh RAG catalog cache from Firestore: %s", exc)

    def build_rag_context(
        self, user_id: Optional[str] = None
    ) -> str:
        """
        Constructs the comprehensive markdown context string injected into Gemini prompt.
        """
        self._refresh_catalog_cache_if_needed()

        sections: List[str] = []

        # 1. Master platform knowledge
        sections.append(CYLIUMOS_MASTER_KNOWLEDGE.strip())

        # 2. Dynamic services catalog from Firestore
        if self._cached_services:
            services_md = ["## Real-Time Dynamic Service Registry (Live from Firestore):"]
            for s in self._cached_services:
                slug = s.get("slug", s.get("id", ""))
                name = s.get("name", slug)
                desc = s.get("description", "")
                cat = s.get("category", "General")
                endpoint = s.get("upstreamApiUrl", "")
                model = s.get("model", "Proprietary Engine")
                services_md.append(
                    f"- **{name}** (Slug: `{slug}` | Category: {cat} | Model: `{model}`)\n"
                    f"  - Description: {desc}\n"
                    f"  - Endpoint: `{endpoint}`"
                )
            sections.append("\n".join(services_md))

        # 3. Dynamic plans catalog from Firestore
        if self._cached_plans:
            plans_md = ["## Real-Time Available Pricing Plans (Live from Firestore):"]
            for p in self._cached_plans:
                p_name = p.get("name", "Standard")
                price_paise = p.get("priceInPaise", 0)
                price_inr = price_paise / 100
                currency = p.get("currency", "INR")
                req_limit = p.get("monthlyRequestLimit", 0)
                rate_limit = p.get("rateLimitPerMinute", 0)
                features = p.get("features", [])
                feats_str = ", ".join(features) if features else "Full API access"
                plans_md.append(
                    f"- **{p_name}**: {currency} {price_inr:,.2f}/mo | "
                    f"{req_limit:,} req/month | {rate_limit} req/min | Features: {feats_str}"
                )
            sections.append("\n".join(plans_md))

        # 4. Authenticated User Profile & Usage Context (if logged in)
        if user_id:
            user_data = fb_service.fetch_user_context(user_id)
            if user_data:
                user_md = [
                    "## Authenticated User Profile & Live Quota (Current Logged-in User):",
                    f"- **User ID**: `{user_id}`",
                ]
                if user_data.get("displayName"):
                    user_md.append(f"- **Name**: {user_data.get('displayName')}")
                if user_data.get("email"):
                    user_md.append(f"- **Email**: {user_data.get('email')}")
                if user_data.get("role"):
                    user_md.append(f"- **Role**: {user_data.get('role')}")

                # Subscriptions
                subs = user_data.get("subscriptions", [])
                if subs:
                    user_md.append("- **Active Subscriptions**:")
                    for sub in subs:
                        user_md.append(
                            f"  - Service: `{sub.get('serviceId')}`, Plan: `{sub.get('planId')}`, Status: **{sub.get('status')}**"
                        )
                else:
                    user_md.append("- **Active Subscriptions**: Free Tier (No active paid subscription)")

                # API Keys
                keys = user_data.get("apiKeys", [])
                if keys:
                    user_md.append(f"- **API Keys**: {len(keys)} key(s) registered")
                    for k in keys:
                        user_md.append(
                            f"  - Key Prefix: `{k.get('keyPrefix')}...`, Env: {k.get('environment')}, Status: {k.get('status')}, Requests Used: {k.get('requestCount', 0)}/{k.get('monthlyLimit', 'Unlimited')}"
                        )
                else:
                    user_md.append("- **API Keys**: No API keys generated yet. User can create one in /dashboard.")

                # Usage Counters
                counters = user_data.get("usageCounters", [])
                if counters:
                    user_md.append("- **Monthly Usage Counters**:")
                    for c in counters:
                        user_md.append(
                            f"  - Service `{c.get('serviceId')}`: {c.get('requestCount', 0)} / {c.get('monthlyLimit', 'unlimited')} requests used"
                        )

                sections.append("\n".join(user_md))
        else:
            sections.append(
                "## User Authentication State:\n"
                "- Current user is **NOT logged in** (Anonymous Guest).\n"
                "- You can invite them to sign up at `/signup` or log in at `/login` to generate API keys, access developer playgrounds, or view their dashboard."
            )

        return "\n\n---\n\n".join(sections)


# Singleton
_rag_service: Optional[RAGContextService] = None


def get_rag_service() -> RAGContextService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGContextService()
    return _rag_service
