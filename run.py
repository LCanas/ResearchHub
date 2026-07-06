"""Entry point for the Collaboration Hub web application.

Run with:  python run.py
Then open  http://127.0.0.1:5000
"""
from hub import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
