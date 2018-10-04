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


class Namespace:

    def __init__(self, name: str):
        self.__name__ = name
        self.__parents__ = {}

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

            if isinstance(obj, Namespace):
                obj.__parents__[self.__name__] = self

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

    def _parent_(self, name, *names):
        parent = self.__parents__[name]

        if names:
            return parent._parent_(*names)

        return parent

    @property
    def __parent__(self):
        try:
            (parent, *remainder) = self.__parents__.values()
        except ValueError:
            return None

        if remainder:
            raise self.MultipleParents(tuple(self.__parents__.keys()))

        return parent

    @property
    def __root__(self):
        # TODO: (immediately) protect against circular references?
        namespace = self
        parent = self.__parent__
        while parent is not None:
            namespace = parent
            parent = namespace.__parent__
        return namespace

    class ReassignmentError(AttributeError):
        pass

    class MultipleParents(ValueError):
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
