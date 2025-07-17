from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"       # Order created but not yet sent to the platform
    OPEN = "open"             # Order sent to the platform, not yet filled
    EXECUTED = "executed"     # Order completely filled
    CANCELED = "canceled"     # Order canceled by user
    FAILED = "failed"         # Order failed to execute
    PARTIALLY_FILLED = "partially_filled" # Order partially filled 