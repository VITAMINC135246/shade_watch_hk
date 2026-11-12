"""Config-driven shade maps on a registered city's native DSM grid."""

__all__ = ['shade_map', 'plan_shade_map']


def __getattr__(name):
    if name in __all__:
        from . import publish
        return getattr(publish, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
