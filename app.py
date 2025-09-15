# Import the Flask tool from the flask package we installed
from flask import Flask

# Create our web application instance
app = Flask(__name__)

# This "decorator" creates a URL route. It's a signpost.
# It says "If someone visits the homepage ('/'), run the function below."
@app.route('/')
def hello_world():
    # This function runs and returns some HTML text to the browser.
    return '<h1>Amy is learning how to vibe code! She is vibing!</h1>'