import os
import shutil
from config import CACHE_DIR, TEMP_DIR, DATA_DIR, LOG_DIR, TEMP_SUBDIRS, DATA_SUBDIRS, LOG_SUBDIRS


###########################################################################
# VERIFY DIRECTORY

def verify_cache():
    # Verify cache dir
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    # Reset temp dir if existing
    if os.path.isdir(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    # Create dirs and sub dirs
    os.mkdir(TEMP_DIR)
    for directory in [LOG_DIR, DATA_DIR]:
        if not os.path.isdir(directory):
            os.mkdir(directory)

    for structure in [DATA_SUBDIRS, LOG_SUBDIRS, TEMP_SUBDIRS]:
        for sub_dir in structure.values():
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)

# ------------------------------ END OF FILE ------------------------------
