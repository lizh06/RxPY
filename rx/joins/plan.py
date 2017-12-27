from .activeplan import ActivePlan
from .joinobserver import JoinObserver


class Plan:
    def __init__(self, expression, mapper):
        self.expression = expression
        self.mapper = mapper

    def activate(self, external_subscriptions, observer, deactivate):
        join_observers = []
        for pattern in self.expression.patterns:
            join_observers.append(self.plan_create_observer(external_subscriptions, pattern, observer.throw))

        def send(*args):
            try:
                result = self.mapper(*args)
            except Exception as e:
                observer.throw(e)
                return
            observer.send(result)

        def close():
            for join_observer in join_observers:
                join_observer.remove_active_plan(active_plan)

            deactivate(active_plan)

        active_plan = ActivePlan(join_observers, send, close)

        for join_observer in join_observers:
            join_observer.add_active_plan(active_plan)

        return active_plan

    def plan_create_observer(self, external_subscriptions, observable, throw):
        entry = external_subscriptions.get(observable)
        if not entry:
            observer = JoinObserver(observable, throw)
            external_subscriptions[observable] = observer
            return observer

        return entry
