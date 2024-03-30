from datetime import datetime
import string
import hashlib
import random


###########################################################################
# GENERAL UTILITY FUNCTIONS
# these will be moved out of utils.py in the future

def get_current_time():
    return datetime.utcnow()


def id_generator(size=10, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def _hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ------------------------------ END OF FILE ------------------------------
