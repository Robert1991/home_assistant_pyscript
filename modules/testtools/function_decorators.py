def pyscript_compile(func):
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner


def service(func):
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner
