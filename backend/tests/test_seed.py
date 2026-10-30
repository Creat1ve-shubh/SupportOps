from app.models import Event, Payment, Subscription
from app.seed import CUSTOMERS, build_records


def records_of(kind):
    return [record for record in build_records() if isinstance(record, kind)]


def test_seed_is_deterministic():
    def snapshot():
        return [
            (type(row).__name__, *(getattr(row, c.key) for c in row.__table__.columns))
            for row in build_records()
        ]

    assert snapshot() == snapshot()


def test_every_customer_has_one_subscription():
    subscriptions = records_of(Subscription)
    assert sorted(s.customer_id for s in subscriptions) == sorted(c.id for c in CUSTOMERS)


def test_upgraded_to_pro_but_still_free_scenario_is_present():
    subscription = next(s for s in records_of(Subscription) if s.customer_id == "cus_1003")
    payment = next(p for p in records_of(Payment) if p.customer_id == "cus_1003")
    assert subscription.plan_code == "free"
    assert (payment.plan_code, payment.status) == ("pro", "succeeded")

    errors = [
        e.event_type for e in records_of(Event)
        if e.customer_id == "cus_1003" and e.severity == "error"
    ]
    assert "webhook.dead_lettered" in errors


def test_events_are_in_chronological_order():
    times = [event.occurred_at for event in records_of(Event)]
    assert times == sorted(times)
