
###########################################################################
# DEFINE EXCEPTIONS

class TdesNotFoundError(Exception):
    """Exception raised for non-existent temporary designation."""

    def __init__(self, field):
        self.message = f"{field} is not a valid temporary designation."
        super().__init__(self.message)


class EphemerisParamsNotSetError(Exception):
    """Exception raised for unset ephemeris API query parameters."""

    def __init__(self):
        self.message = f"The API query parameters for the Ephemeris object have not been set."
        super().__init__(self.message)


class OutdatedParamsError(Exception):
    """Exception raised for outdated ephemeris API query parameters."""

    def __init__(self):
        self.message = f"Update required for outdated Ephemeris object API query parameters."
        super().__init__(self.message)


class ImageCountExceededError(Exception):
    """Exception raised when too many images would be required to locate an NEO."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ObjectNotVisibleError(Exception):
    """Exception raised when an NEO is not currently visible."""

    def __init__(self, field):
        self.message = f"{field} is not currently visible from the observatory location."
        super().__init__(self.message)


# ------------------------------ END OF FILE ------------------------------
