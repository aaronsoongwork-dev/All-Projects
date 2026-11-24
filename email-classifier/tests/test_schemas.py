import typing

from emailclf import config
from emailclf.schemas import LLMClassification


def test_literal_labels_match_config():
    allowed = set(typing.get_args(LLMClassification.model_fields["label"].annotation))
    assert allowed == set(config.LABELS)
