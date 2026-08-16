from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

DEFAULT_THRESHOLDS_SECONDS = {
    "runtime-sensitive": 6*3600,
    "release-bound": 7*86400,
    "model-bound": 30*86400,
    "strategy-bound": 90*86400,
    "stable": None,
    "historical": None,
}

@dataclass(frozen=True)
class Freshness:
    state: str
    age_seconds: float | None
    reason: str

def _parse_dt(value):
    if not isinstance(value,str) or not value.strip(): return None
    try:
        dt=datetime.fromisoformat(value.strip().replace("Z","+00:00"))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None

def evaluate(meta, now=None):
    now=now or datetime.now(timezone.utc)
    cls=meta.get("freshness_class")
    if cls in {"stable","historical"}:
        return Freshness("NOT_APPLICABLE",None,f"{cls} has no wall-clock expiry")
    threshold=DEFAULT_THRESHOLDS_SECONDS.get(str(cls))
    if threshold is None:
        return Freshness("UNKNOWN",None,f"unknown or missing freshness_class={cls!r}")
    stamp=_parse_dt(meta.get("last_verified") or meta.get("verified_at") or meta.get("observed_at"))
    if not stamp:
        return Freshness("UNKNOWN",None,"no verification/observation timestamp")
    age=max(0.0,(now-stamp).total_seconds())
    if age<=threshold: return Freshness("CURRENT",age,"within threshold")
    if age<=threshold*1.5: return Freshness("DUE",age,"verification due")
    return Freshness("STALE",age,"verification expired")
