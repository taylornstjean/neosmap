
###########################################################################
# DEFINE EXCEPTIONS

class NotAPositiveIntegerError(Exception):
    """Exception raised for negative and/or non-integer input where a positive integer is required."""

    def __init__(self, field):
        self.message = f"{field} must be a non-zero positive integer value."
        super().__init__(self.message)


class InvalidFilterError(Exception):
    """Exception raised for invalid filter selection."""

    def __init__(self):
        self.message = "Filter must be one of bg40, r, v."
        super().__init__(self.message)


class InvalidDatetimeError(Exception):
    """Exception raised for invalid datetime input."""

    def __init__(self):
        self.message = ("Observation start time must be later than the current time. (Backend "
                        "request format 'YYYY-MM-DDThh:mm')")
        super().__init__(self.message)

# ------------------------------ END OF FILE ------------------------------
