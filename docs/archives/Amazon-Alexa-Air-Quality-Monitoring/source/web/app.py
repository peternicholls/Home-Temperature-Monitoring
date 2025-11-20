from flask import Flask, render_template, jsonify
import logging
import sys
import os

# Add the project root to the python path so we can import from source
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from source.collectors.amazon_auth import run_amazon_login

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/api/amazon/login', methods=['POST'])
def amazon_login():
    try:
        cookies = run_amazon_login()
        if cookies:
            # Save cookies to secrets.yaml
            import yaml
            secrets_path = os.path.join(os.path.dirname(__file__), '../../config/secrets.yaml')
            
            # Read existing secrets
            try:
                with open(secrets_path, 'r') as f:
                    secrets = yaml.safe_load(f) or {}
            except FileNotFoundError:
                secrets = {}
            
            # Update amazon_aqm section
            if 'amazon_aqm' not in secrets:
                secrets['amazon_aqm'] = {}
            secrets['amazon_aqm']['cookies'] = cookies
            
            # Write back to file
            with open(secrets_path, 'w') as f:
                yaml.dump(secrets, f, default_flow_style=False)
            
            logger.info(f"Saved {len(cookies)} cookies to {secrets_path}")
            return jsonify({"status": "success", "message": f"Login successful! Saved {len(cookies)} cookies.", "cookies_count": len(cookies)})
        else:
            return jsonify({"status": "error", "message": "Login failed or cancelled"}), 400
    except Exception as e:
        logger.error(f"Error during Amazon login: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
