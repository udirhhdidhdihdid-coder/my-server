import os
from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/generate-code', methods=['GET'])
def generate_code():
    code = str(random.randint(100000, 999999))
    return jsonify({
        "success": True,
        "code": code
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
