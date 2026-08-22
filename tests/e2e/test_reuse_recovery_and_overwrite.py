from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE


def test_resume_sequence_is_fixed() -> None:
    assert RESUME_SEQUENCE[0] == "validate required existing artifacts"
    assert RESUME_SEQUENCE[-1] == "atomically publish completed outputs"
