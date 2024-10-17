from usniffs import Sniffs


class SingletonDNEError(Exception):
    ...


def singleton(cls):
    """Singleton decorator for classes. Use this instead of globals where possible."""
    instance = None

    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return getinstance


@singleton
class SniffsSingleton(Sniffs):
    ...


def get_sniffs() -> SniffsSingleton:
    return SniffsSingleton()