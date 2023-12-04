import os
import shutil
from config import (
    CACHE_DIR,
    CACHE_TEMP_DIR,
    CACHE_USER_DIR,
    CACHE_DATA_DIR,
    CACHE_LOG_DIR,
    TEMP_SUBDIRS,
    DATA_SUBDIRS,
    LOG_SUBDIRS,
    CACHE_OBJECT_DIR
)


###########################################################################
# VERIFY DIRECTORY

def verify_cache():
    # Verify cache dir
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    # Reset temp dir if existing
    if os.path.isdir(CACHE_TEMP_DIR):
        shutil.rmtree(CACHE_TEMP_DIR)

    # Create dirs and sub dirs
    os.mkdir(CACHE_TEMP_DIR)
    for directory in [CACHE_LOG_DIR, CACHE_DATA_DIR, CACHE_OBJECT_DIR, CACHE_USER_DIR]:
        if not os.path.isdir(directory):
            os.mkdir(directory)

    for structure in [DATA_SUBDIRS, LOG_SUBDIRS, TEMP_SUBDIRS]:
        for sub_dir in structure.values():
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)

# ------------------------------ END OF FILE ------------------------------
