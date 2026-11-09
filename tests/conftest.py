import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_collection.synthetic import generate_security_events, generate_survey, generate_transactions  # noqa: E402


@pytest.fixture(scope="session")
def tx():
    return generate_transactions(n=8000, n_customers=800, fraud_rate=0.03, days=30, seed=7, end_date="2025-06-30")


@pytest.fixture(scope="session")
def events():
    return generate_security_events(n=3000, days=30, seed=7, end_date="2025-06-30")


@pytest.fixture(scope="session")
def survey():
    return generate_survey(n=300, seed=7, salt="test-salt")


@pytest.fixture(scope="session")
def cfg():
    from src.common import load_settings
    return load_settings()
