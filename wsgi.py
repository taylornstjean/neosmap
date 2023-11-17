from neosmap.web_interface.app import app
from sys import platform

if __name__ == "__main__":
    PORT = 5200 if platform == "darwin" else 5000
    app.run(host="0.0.0.0", port=PORT)
