import types
from typing import Callable, Any
from abc import abstractmethod

from rx import config
from rx.concurrency import current_thread_scheduler

from . import Observer, Disposable, bases
from .anonymousobserver import AnonymousObserver
from .autodetachobserver import AutoDetachObserver


class Observable(bases.Observable):
    """Represents a push-style collection."""

    def __init__(self):
        self.lock = config["concurrency"].RLock()

        # Deferred instance method assignment
        for name, method in self._methods:
            setattr(self, name, types.MethodType(method, self))

    def __or__(self, other):
        return other(self)

    def subscribe(self, on_next=None, on_error=None, on_completed=None, observer=None):
        """Subscribe an observer to the observable sequence.

        Examples:
        1 - source.subscribe()
        2 - source.subscribe(observer)
        3 - source.subscribe(on_next)
        4 - source.subscribe(on_next, on_error)
        5 - source.subscribe(on_next, on_error, on_completed)

        Keyword arguments:
        on_next -- [Optional] Action to invoke for each element in the
            observable sequence.
        on_error -- [Optional] Action to invoke upon exceptional
            termination of the observable sequence.
        on_completed -- [Optional] Action to invoke upon graceful
            termination of the observable sequence.
        observer -- [Optional] The object that is to receive
            notifications. You may subscribe using an observer or
            callbacks, not both.

        Return disposable object representing an observer's subscription
            to the observable sequence.
        """
        # Accept observer as first parameter
        if isinstance(on_next, Observer):
            observer = on_next
        elif hasattr(on_next, "on_next") and callable(on_next.on_next):
            observer = on_next
        elif not observer:
            observer = AnonymousObserver(on_next, on_error, on_completed)

        auto_detach_observer = AutoDetachObserver(observer)

        def fix_subscriber(subscriber):
            """Fixes subscriber to make sure it returns a Disposable instead
            of None or a dispose function"""

            if not hasattr(subscriber, "dispose"):
                subscriber = Disposable.create(subscriber)

            return subscriber

        def set_disposable(scheduler=None, value=None):
            try:
                subscriber = self._subscribe_core(auto_detach_observer)
            except Exception as ex:  # By design. pylint: disable=W0703
                if not auto_detach_observer.fail(ex):
                    raise
            else:
                auto_detach_observer.disposable = fix_subscriber(subscriber)

        # Subscribe needs to set up the trampoline before for subscribing.
        # Actually, the first call to Subscribe creates the trampoline so
        # that it may assign its disposable before any observer executes
        # OnNext over the CurrentThreadScheduler. This enables single-
        # threaded cancellation
        # https://social.msdn.microsoft.com/Forums/en-US/eb82f593-9684-4e27-
        # 97b9-8b8886da5c33/whats-the-rationale-behind-how-currentthreadsche
        # dulerschedulerequired-behaves?forum=rx
        if current_thread_scheduler.schedule_required():
            current_thread_scheduler.schedule(set_disposable)
        else:
            set_disposable()

        # Hide the identity of the auto detach observer
        return Disposable.create(auto_detach_observer.dispose)

    @abstractmethod
    def _subscribe_core(self, observer):
        return NotImplemented

    def map(self, mapper: Callable[[Any], Any]) -> "Observable":
        """Project each element of an observable sequence into a new form
        by incorporating the element's index.

        1 - source.map(lambda value: value * value)

        Keyword arguments:
        mapper -- A transform function to apply to each source element; the
            second parameter of the function represents the index of the
            source element.

        Returns an observable sequence whose elements are the result of
        invoking the transform function on each element of source.
        """

        from ..operators.observable.map import map
        source = self
        return map(mapper, source)

    def map_indexed(self, mapper: Callable[[Any, int], Any]) -> "Observable":
        from ..operators.observable.map import map_indexed
        source = self
        return map_indexed(mapper, source)

    def filter(self, predicate: Callable[[Any], bool]) -> "Observable":
        """Filters the elements of an observable sequence based on a
        predicate.

        1 - source.filter(lambda value: value < 10)

        Keyword arguments:
        predicate -- A function to test each source element for a
            condition.

        Returns an observable sequence that contains elements from the
        input sequence that satisfy the condition.
        """
        from ..operators.observable.filter import filter
        source = self
        return filter(predicate, source)

    def filter_indexed(self, predicate: Callable[[Any, int], bool]) -> "Observable":
        """Filters the elements of an observable sequence based on a
        predicate by incorporating the element's index.

        1 - source.filter(lambda value, index: value < 10 or index < 10)

        Keyword arguments:
        predicate - A function to test each source element for a
            condition; the second parameter of the function represents
            the index of the source element.

        Returns an observable sequence that contains elements from the
        input sequence that satisfy the condition.
        """

        from ..operators.observable.filter import filter_indexed
        source = self
        return filter_indexed(predicate, source)

    def skip(self, count: int) -> "Observable":
        """Bypasses a specified number of elements in an observable sequence
        and then returns the remaining elements.

        Keyword arguments:
        count -- The number of elements to skip before returning the remaining
            elements.

        Returns an observable sequence that contains the elements that occur
        after the specified index in the input sequence.
        """
        from ..operators.observable.skip import skip
        source = self
        return skip(count, source)
