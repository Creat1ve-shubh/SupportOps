"""Deterministic synthetic seed records.

Run with `uv run python -m app.seed`. Each run truncates the support tables and inserts the
same rows, so investigations always start from a known state. Explanations of what each
scenario means belong in held-out answer keys, never in these rows.
"""

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, get_engine
from app.models import Customer, Event, Payment, Plan, Subscription, SupportTicket


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


PLANS = [
    Plan(code="free", name="Free", monthly_price_cents=0, price_id=None),
    Plan(code="pro", name="Pro", monthly_price_cents=1900, price_id="price_pro_monthly"),
    Plan(code="team", name="Team", monthly_price_cents=4900, price_id="price_team_monthly"),
]

CUSTOMERS = [
    Customer(id="cus_1001", email="avery.chen@example.com", name="Avery Chen",
             created_at=_at("2026-03-02T15:20:00")),
    Customer(id="cus_1002", email="jordan.okafor@example.com", name="Jordan Okafor",
             created_at=_at("2026-05-11T08:03:00")),
    Customer(id="cus_1003", email="priya.raman@example.com", name="Priya Raman",
             created_at=_at("2026-06-14T19:47:00")),
    Customer(id="cus_1004", email="mateo.silva@example.com", name="Mateo Silva",
             created_at=_at("2026-01-27T11:12:00")),
    Customer(id="cus_1005", email="sam.whitfield@example.com", name="Sam Whitfield",
             created_at=_at("2026-09-03T21:30:00")),
    Customer(id="cus_1006", email="lena.fischer@example.com", name="Lena Fischer",
             created_at=_at("2026-07-22T06:55:00")),
]


def _subscription(sub_id, customer_id, plan_code, start, end, created, updated):
    return Subscription(
        id=sub_id, customer_id=customer_id, plan_code=plan_code, status="active",
        current_period_start=_at(start), current_period_end=_at(end) if end else None,
        created_at=_at(created), updated_at=_at(updated),
    )


SUBSCRIPTIONS = [
    _subscription("sub_1001", "cus_1001", "pro", "2026-10-01T00:00:00", "2026-11-01T00:00:00",
                  "2026-03-02T15:20:00", "2026-10-01T00:00:04"),
    _subscription("sub_1002", "cus_1002", "free", "2026-05-11T08:03:00", None,
                  "2026-05-11T08:03:00", "2026-05-11T08:03:00"),
    # Still Free although a Pro payment succeeded on 2026-10-20.
    _subscription("sub_1003", "cus_1003", "free", "2026-06-14T19:47:00", None,
                  "2026-06-14T19:47:00", "2026-06-14T19:47:00"),
    _subscription("sub_1004", "cus_1004", "team", "2026-10-15T00:00:00", "2026-11-15T00:00:00",
                  "2026-01-27T11:12:00", "2026-10-15T00:00:03"),
    _subscription("sub_1005", "cus_1005", "free", "2026-09-03T21:30:00", None,
                  "2026-09-03T21:30:00", "2026-09-03T21:30:00"),
    _subscription("sub_1006", "cus_1006", "pro", "2026-10-20T09:12:41", "2026-11-20T09:12:41",
                  "2026-07-22T06:55:00", "2026-10-20T09:12:44"),
]


def _payment(pay_id, customer_id, plan_code, status, created, reference, failure_reason=None):
    plan = next(plan for plan in PLANS if plan.code == plan_code)
    return Payment(
        id=pay_id, customer_id=customer_id, subscription_id=f"sub_{customer_id[4:]}",
        plan_code=plan_code, price_id=plan.price_id, amount_cents=plan.monthly_price_cents,
        currency="usd", status=status, failure_reason=failure_reason,
        provider_reference=reference, created_at=_at(created),
    )


PAYMENTS = [
    _payment("pay_2001", "cus_1001", "pro", "succeeded", "2026-09-01T00:00:02", "ch_3Q8aVb01"),
    _payment("pay_2002", "cus_1001", "pro", "succeeded", "2026-10-01T00:00:02", "ch_3Q9kLm02"),
    _payment("pay_2003", "cus_1004", "team", "succeeded", "2026-10-15T00:00:01", "ch_3QAx7r03"),
    _payment("pay_2004", "cus_1005", "pro", "failed", "2026-10-19T17:04:51", "ch_3QBd2s04",
             failure_reason="card_declined: insufficient_funds"),
    _payment("pay_2005", "cus_1006", "pro", "succeeded", "2026-10-20T09:12:39", "ch_3QBf9t05"),
    _payment("pay_2006", "cus_1003", "pro", "succeeded", "2026-10-20T09:41:07", "ch_3QBg4u06"),
]


def _event(occurred, customer_id, source, event_type, severity, message, **payload):
    return Event(
        occurred_at=_at(occurred), customer_id=customer_id, source=source,
        event_type=event_type, severity=severity, message=message, payload=payload,
    )


def _successful_upgrade(customer_id, sub_id, pay_id, reference, provider_event, times):
    checkout, paid, received, updated = times
    return [
        _event(checkout, customer_id, "app", "checkout.started", "info",
               "Checkout session opened for plan pro", plan="pro", price_id="price_pro_monthly"),
        _event(paid, customer_id, "billing", "payment.succeeded", "info",
               f"Charge {reference} succeeded for 1900 usd", payment_id=pay_id,
               provider_reference=reference),
        _event(received, customer_id, "webhooks", "webhook.received", "info",
               f"Received payment.succeeded webhook {provider_event}",
               provider_event_id=provider_event, attempt=1),
        _event(updated, customer_id, "entitlements", "entitlement.updated", "info",
               f"Subscription {sub_id} plan changed free -> pro",
               subscription_id=sub_id, provider_event_id=provider_event,
               from_plan="free", to_plan="pro"),
    ]


EVENTS = sorted(
    [
        _event("2026-10-01T00:00:02", "cus_1001", "billing", "payment.succeeded", "info",
               "Charge ch_3Q9kLm02 succeeded for 1900 usd", payment_id="pay_2002",
               provider_reference="ch_3Q9kLm02"),
        _event("2026-10-01T00:00:04", "cus_1001", "entitlements", "subscription.renewed", "info",
               "Subscription sub_1001 renewed on plan pro", subscription_id="sub_1001"),
        _event("2026-10-15T00:00:03", "cus_1004", "entitlements", "subscription.renewed", "info",
               "Subscription sub_1004 renewed on plan team", subscription_id="sub_1004"),
        _event("2026-10-19T17:04:12", "cus_1005", "app", "checkout.started", "info",
               "Checkout session opened for plan pro", plan="pro", price_id="price_pro_monthly"),
        _event("2026-10-19T17:04:51", "cus_1005", "billing", "payment.failed", "warning",
               "Charge ch_3QBd2s04 failed: card_declined (insufficient_funds)",
               payment_id="pay_2004", provider_reference="ch_3QBd2s04"),
        *_successful_upgrade(
            "cus_1006", "sub_1006", "pay_2005", "ch_3QBf9t05", "evt_7Hc2Lw05",
            ("2026-10-20T09:11:58", "2026-10-20T09:12:39", "2026-10-20T09:12:40",
             "2026-10-20T09:12:44"),
        ),
        _event("2026-10-20T09:40:22", "cus_1003", "app", "checkout.started", "info",
               "Checkout session opened for plan pro", plan="pro", price_id="price_pro_monthly"),
        _event("2026-10-20T09:41:07", "cus_1003", "billing", "payment.succeeded", "info",
               "Charge ch_3QBg4u06 succeeded for 1900 usd", payment_id="pay_2006",
               provider_reference="ch_3QBg4u06"),
        _event("2026-10-20T09:41:08", "cus_1003", "webhooks", "webhook.received", "info",
               "Received payment.succeeded webhook evt_7Hd9Qx06",
               provider_event_id="evt_7Hd9Qx06", attempt=1),
        _event("2026-10-20T09:41:13", "cus_1003", "entitlements", "entitlement.update_failed",
               "error", "Timed out after 5000 ms acquiring row lock on subscription sub_1003",
               subscription_id="sub_1003", provider_event_id="evt_7Hd9Qx06", attempt=1),
        _event("2026-10-20T09:41:13", "cus_1003", "webhooks", "webhook.retry_scheduled",
               "warning", "Retrying webhook evt_7Hd9Qx06 in 60 s",
               provider_event_id="evt_7Hd9Qx06", next_attempt=2),
        _event("2026-10-20T09:42:18", "cus_1003", "entitlements", "entitlement.update_failed",
               "error", "Timed out after 5000 ms acquiring row lock on subscription sub_1003",
               subscription_id="sub_1003", provider_event_id="evt_7Hd9Qx06", attempt=2),
        _event("2026-10-20T09:42:18", "cus_1003", "webhooks", "webhook.retry_scheduled",
               "warning", "Retrying webhook evt_7Hd9Qx06 in 240 s",
               provider_event_id="evt_7Hd9Qx06", next_attempt=3),
        _event("2026-10-20T09:46:23", "cus_1003", "entitlements", "entitlement.update_failed",
               "error", "Timed out after 5000 ms acquiring row lock on subscription sub_1003",
               subscription_id="sub_1003", provider_event_id="evt_7Hd9Qx06", attempt=3),
        _event("2026-10-20T09:46:23", "cus_1003", "webhooks", "webhook.dead_lettered", "error",
               "Webhook evt_7Hd9Qx06 moved to dead-letter queue after 3 attempts",
               provider_event_id="evt_7Hd9Qx06", attempts=3),
        _event("2026-10-20T09:52:30", "cus_1003", "app", "account.viewed", "info",
               "Account page rendered with plan free", plan="free"),
    ],
    key=lambda event: event.occurred_at,
)

TICKETS = [
    SupportTicket(
        id="tkt_5001", customer_id="cus_1001", status="resolved",
        subject="Where can I download invoices?",
        body="Hi, I need PDF invoices for September for my accountant. Where do I find them?",
        created_at=_at("2026-09-04T13:18:00"),
    ),
    SupportTicket(
        id="tkt_5002", customer_id="cus_1003", status="open",
        subject="I upgraded to Pro but my account still shows Free",
        body=(
            "Hi, I upgraded to Pro about 15 minutes ago and I was charged $19.00, but my "
            "account page still says Free and I can't use any Pro features. Can you fix this?"
        ),
        created_at=_at("2026-10-20T09:55:02"),
    ),
]


def build_records() -> list[Base]:
    """Fresh copies of every seed row, in foreign-key insertion order."""
    templates = [*PLANS, *CUSTOMERS, *SUBSCRIPTIONS, *PAYMENTS, *EVENTS, *TICKETS]
    return [
        type(row)(**{column.key: getattr(row, column.key) for column in row.__table__.columns})
        for row in templates
    ]


def seed(session: Session) -> None:
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    # The models declare no relationships, so flush per table to respect foreign keys.
    records = build_records()
    for table in Base.metadata.sorted_tables:
        session.add_all(record for record in records if record.__table__ is table)
        session.flush()


def main() -> None:
    with Session(get_engine()) as session, session.begin():
        seed(session)
    print(
        f"Seeded {len(CUSTOMERS)} customers, {len(PAYMENTS)} payments, "
        f"{len(EVENTS)} events and {len(TICKETS)} tickets."
    )


if __name__ == "__main__":
    main()
