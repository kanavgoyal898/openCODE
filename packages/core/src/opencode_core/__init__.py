"""Standalone openCODE engine contracts.

Feature implementations are added in roadmap order.  This package deliberately
has no dependency on the API, database, workers, or web application.
"""

from opencode_core.config import CoreSettings
from opencode_core.version import PACKAGE_VERSION

__all__ = ["PACKAGE_VERSION", "CoreSettings"]
