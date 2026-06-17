import pytest


@pytest.fixture
def created_datasets(textual):
    """Track datasets created during a test so they are cleaned up afterwards.

    Tests should append each newly-created dataset name to the yielded list.
    On teardown the fixture deletes every registered dataset, swallowing
    per-dataset errors so a single failure does not mask others. This keeps
    tests from leaking state into the shared backend used by the CI matrix.
    """
    names = []
    yield names
    for name in names:
        try:
            textual.delete_dataset(name)
        except Exception:
            pass
