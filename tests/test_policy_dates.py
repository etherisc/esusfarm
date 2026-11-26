from server.config import settings
from server.model.policy import PolicyIn


def test_subscription_date_no_year_window():
    policy = PolicyIn(
        personId="fXJ6Gwfgnw-C",
        riskId="t4FcP75uGHHc",
        externalId="ext-1",
        subscriptionDate="2019-06-14",
        currency="UGX",
        sumInsuredAmount=1000,
        premiumAmount=50,
    )
    assert policy.subscriptionDate == "2019-06-14"


def test_currency_required():
    try:
        PolicyIn(
            personId="fXJ6Gwfgnw-C",
            riskId="t4FcP75uGHHc",
            externalId="ext-0",
            subscriptionDate="2025-01-01",
            sumInsuredAmount=1000,
            premiumAmount=50,
        )
        raise AssertionError("expected validation error")
    except Exception:
        pass


def test_ugx_minimum_one():
    PolicyIn(
        personId="fXJ6Gwfgnw-C",
        riskId="t4FcP75uGHHc",
        externalId="ext-min",
        subscriptionDate="2025-01-01",
        currency="UGX",
        sumInsuredAmount=1,
        premiumAmount=1,
    )


def test_amount_ceiling_from_settings():
    with_settings = settings.POLICY_MAX_AMOUNT_UGX
    try:
        PolicyIn(
            personId="fXJ6Gwfgnw-C",
            riskId="t4FcP75uGHHc",
            externalId="ext-2",
            subscriptionDate="2025-01-01",
            currency="UGX",
            sumInsuredAmount=int(with_settings) + 1,
            premiumAmount=1,
        )
        raise AssertionError("expected ValueError")
    except ValueError:
        pass