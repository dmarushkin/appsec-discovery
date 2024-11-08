from flask import Flask, request

app = Flask(__name__)

# Define a route that accepts both GET and POST requests
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        # Handle POST request
        return 'Handling POST request'
    else:
        # Handle GET request
        return 'Handling GET request'

# Define a route that accepts both GET and POST requests
@app.route('/get')
def get():
        # Handle GET request
        return 'Handling GET request'

if __name__ == '__main__':
    app.run(debug=True)