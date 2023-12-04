
###########################################################################
# DEFINE EXCEPTIONS

class CacheTimeExceededError(Exception):
    """Exception raised for out-of-date cache data."""

    def __init__(self, field):
        self.message = f"{field} data has exceeded its maximum cache time."
        super().__init__(self.message)

# ------------------------------ END OF FILE ------------------------------
