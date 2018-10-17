"""Flexible & precise namespace declaration

WARNING: This is Python. Use modules!

Intended to work like modules -- on steroids.

"""
# TODO: document
# TODO: test
# TODO: ???

import dataclasses
import functools
import typing


# TODO: Perhaps: Namespace class API
#
# Similar to Enum, could treat existing interface as functional API, and
# supply a class inheritance interface.
#
# (That said, this may or may not work internally the same as Enum.)
#
# This way, if desired, namespace declaration could take the form:
#
#    class User(Namespace):
#
#       foo = 'bar'
#
#       def add(name):
#           ...
#
# and be equivalent to the current:
#
#   UserNamespace = Namespace('user')
#
#   UserNamespace.foo = 'bar'
#
#   @UserNamespace
#   def add(name):
#       ...


class Namespace:

    def __init__(self, name: str):
        self.__name__ = name

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__name__!r})'

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise self.ReassignmentError(key)

        super().__setattr__(key, value)

    def _update_(self, *bases, **updates):
        if len(bases) > 1:
            raise TypeError('_update_ expected at most 1 arguments, got 2')

        for source in (bases + (updates,)):
            stream = source
            if hasattr(source, 'keys'):
                stream = ((key, source[key]) for key in source.keys())

            for (key, value) in stream:
                setattr(self, key, value)

    def _add_(self, *named):
        for obj in named:
            setattr(self, obj.__name__, obj)

    def _staticmethod_(self, func):
        self._add_(func)
        return func

    def _method_(self, func):
        nfunc = NamespaceMethod(self, func)
        self._add_(nfunc)
        return nfunc

    def __call__(self, named):
        self._add_(named)
        return named

    class ReassignmentError(AttributeError):
        pass


# NOTE: We would get NamespaceMethod "for free" if concrete namespaces were
# (sub)classes and entities added to their class dicts; however, not sure
# that's the most expedient.

@dataclasses.dataclass(frozen=True)
class NamespaceMethod:

    __self__: Namespace
    __func__: typing.Callable

    def __post_init__(self):
        self.__dict__.update(
            (name, getattr(self.__func__, name))
            for name in functools.WRAPPER_ASSIGNMENTS
        )
        self.__dict__.update(self.__func__.__dict__)

    def __call__(self, *args, **kwargs):
        return self.__func__(self.__self__, *args, **kwargs)
