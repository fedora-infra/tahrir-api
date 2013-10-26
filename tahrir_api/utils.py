""" Module to keep random utils. """


def autocommit(func):
    """ A decorator that autocommits after API calls unless
    configured otherwise.
    """

    def _wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if self.autocommit:
            self.session.commit()
        return result

    _wrapper.__name__ = func.__name__
    _wrapper.__doc__ = func.__doc__

    return _wrapper
