from neosmap.web_interface.main.routes import mod_main

###########################################################################
# INITIALIZE JINJA2

import jinja2
import os

template_dir = os.path.join(os.path.abspath(__file__), "../..", "main_templates")
loader = jinja2.FileSystemLoader(template_dir)
environment = jinja2.Environment(loader=loader)

# ------------------------------ END OF FILE ------------------------------
