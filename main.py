from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "bot": "Spam Shield Bot",
        "version": "2.0",
        "developer": "@rehuux",
        "owner": "Syed Rehan"
    })

@app.route('/ping')
def ping():
    return "pong"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
