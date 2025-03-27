import pytest

from amads.harmony.root_finding.parncutt_1988 import root


def test_empty_chord():
    with pytest.raises(ValueError):
        root([])
