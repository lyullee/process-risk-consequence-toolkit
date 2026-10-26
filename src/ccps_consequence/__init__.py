# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ugwiyeon Lee
"""Independent consequence screening API; not a CCPS conformity claim."""
from .api import calculate, verify_receipt, UnsupportedCalculation
from .catalog import calculation_catalog, contract_schemas
from .contracts import Context, Evidence, Receipt

__version__ = "0.1.0"
__all__ = ["calculate", "verify_receipt", "UnsupportedCalculation", "calculation_catalog",
           "contract_schemas", "Context", "Evidence", "Receipt"]
