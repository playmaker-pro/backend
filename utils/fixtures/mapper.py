import pytest

from mapper.models import Mapper


@pytest.fixture
def mapper():
    """Create a mapper instance."""

    return Mapper.objects.create()
