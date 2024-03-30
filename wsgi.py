from neosmap.web_interface.app import app


###########################################################################
# WSGI ENTRY POINT

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["FLASK_RUN_PORT"])

# ------------------------------ END OF FILE ------------------------------
