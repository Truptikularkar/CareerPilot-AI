import pytest
from careerpilot.interview.followups import FollowUpEngine


def test_followup_engine_chains():
    # BigQuery chain
    chain_bq = FollowUpEngine.generate_followup_chain("BigQuery Architecture")
    assert len(chain_bq) == 4
    assert any("partitioning" in f.lower() for f in chain_bq)

    # Airflow chain
    chain_af = FollowUpEngine.generate_followup_chain("Airflow Operations")
    assert len(chain_af) == 4
    assert any("idempotent" in f.lower() for f in chain_af)

    # Generic chain
    chain_gen = FollowUpEngine.generate_followup_chain("Generic Microservices")
    assert len(chain_gen) == 4
