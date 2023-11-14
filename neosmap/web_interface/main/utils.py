from .exceptions import NotAPositiveIntegerError, InvalidDatetimeError, InvalidFilterError
import re
import datetime


###########################################################################
# SCRIPTING INPUT VERIFICATION

def verify_script_args(**kwargs):
    for field, value in kwargs.items():
        if field in ["binning", "image_delay", "exposure_time", "blink_count"]:
            if not re.match(r"^[0-9]*[1-9][0-9]*$", value):
                raise NotAPositiveIntegerError(field.capitalize())

        elif field == "observe_start":
            if value == "" or not value:
                continue
            try:
                observe_time = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M").timestamp()
            except ValueError:
                raise InvalidDatetimeError
            current_time = datetime.datetime.utcnow().timestamp()
            if current_time > observe_time:
                raise InvalidDatetimeError

        elif field == "filter":
            if value not in ["bg40", "r", "v"]:
                raise InvalidFilterError

        else:
            pass

# ------------------------------ END OF FILE ------------------------------
