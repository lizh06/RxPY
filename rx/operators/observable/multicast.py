from rx.core import ObservableBase, AnonymousObservable, ConnectableObservable
from rx.disposables import CompositeDisposable


def multicast(source: ObservableBase, subject=None, subject_mapper=None,
              mapper=None) -> ObservableBase:
    """Multicasts the source sequence notifications through an instantiated
    subject into all uses of the sequence within a mapper function. Each
    subscription to the resulting sequence causes a separate multicast
    invocation, exposing the sequence resulting from the mapper function's
    invocation. For specializations with fixed subject types, see Publish,
    PublishLast, and Replay.

    Example:
    1 - res = source.multicast(observable)
    2 - res = source.multicast(subject_mapper=lambda scheduler: Subject(),
                               mapper=lambda x: x)

    Keyword arguments:
    subject_mapper -- Factory function to create an intermediate
        subject through which the source sequence's elements will be
        multicast to the mapper function.
    subject -- Subject to push source elements into.
    mapper -- [Optional] Optional mapper function which can use the
        multicasted source sequence subject to the policies enforced
        by the created subject. Specified only if subject_mapper" is a
        factory function.

    Returns an observable sequence that contains the elements of a
    sequence produced by multicasting the source sequence within a
    mapper function.
    """

    if subject_mapper:
        def subscribe(observer, scheduler=None):
            connectable = source.multicast(subject=subject_mapper(scheduler))
            return CompositeDisposable(mapper(connectable).subscribe(observer, scheduler), connectable.connect(scheduler))
        return AnonymousObservable(subscribe)

    return ConnectableObservable(source, subject)
