from flask import Flask, render_template, jsonify, request
import logging
import sys
import os
import yaml

# Add the project root to the python path so we can import from source
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from source.collectors.amazon_auth import run_amazon_login
from source.config.loader import load_config

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
        # Get domain from request body, config, or default to amazon.co.uk
        data = request.get_json() or {}
        domain = data.get('domain')
        
        if not domain:
            # Try to load from config
            try:
                config = load_config()
                domain = config.get('collectors', {}).get('amazon_aqm', {}).get('domain') or \
                        config.get('amazon_aqm', {}).get('domain')
            except Exception as e:
                logger.warning(f"Could not load config for domain: {e}")
                domain = None
        
        # Default to amazon.co.uk if not found
        if not domain:
            domain = 'amazon.co.uk'
        
        logger.info(f"Starting Amazon login for domain: {domain}")
        
        # Run login with specified domain
        cookies = run_amazon_login(domain=domain)
        
        if cookies:
            # Save cookies to secrets.yaml
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
            secrets['amazon_aqm']['domain'] = domain  # Store domain for reference
            
            # Write back to file
            with open(secrets_path, 'w') as f:
                yaml.dump(secrets, f, default_flow_style=False)
            
            logger.info(f"Saved {len(cookies)} cookies to {secrets_path} for domain: {domain}")
            return jsonify({
                "status": "success",
                "message": f"Login successful! Saved {len(cookies)} cookies for {domain}.",
                "cookies_count": len(cookies),
                "domain": domain
            })
        else:
            return jsonify({"status": "error", "message": "Login failed or cancelled"}), 400
    except Exception as e:
        logger.error(f"Error during Amazon login: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
