"""Invalida caches de indicadores após mudanças nos dados."""

from app.services.cache_ttl import cache_clear_prefix


def invalidate_indicator_caches() -> None:
    cache_clear_prefix("analytics:")
    cache_clear_prefix("dossie:")
