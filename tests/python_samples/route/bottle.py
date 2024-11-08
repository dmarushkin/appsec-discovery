from bottle import route, get, run

@route('/hello')
def hello():
    return "Hello World!"

@get('/get')
def hello():
    return "Hello World!"

run(host='localhost', port=8080, debug=True)