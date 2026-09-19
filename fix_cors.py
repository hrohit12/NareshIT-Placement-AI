import re
with open('app.py', 'r') as f:
    code = f.read()

# Add flask-cors if not there
if 'from flask_cors import CORS' not in code:
    code = code.replace('from flask import Flask', 'from flask import Flask\nfrom flask_cors import CORS')
    code = code.replace('app = Flask(__name__', 'app = Flask(__name__\nCORS(app)')

with open('app.py', 'w') as f:
    f.write(code)
