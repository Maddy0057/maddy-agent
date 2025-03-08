import google.generativeai as genai
from flask import Flask, request, jsonify, render_template_string
import os
import markdown
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

app = Flask(__name__)

# Load API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("API key not found. Set GOOGLE_API_KEY in your environment.")
model_name = 'gemini-2.0-flash'
model = genai.GenerativeModel(model_name)  # Simplified, no configure() needed

# Backstory for Maddy
backstory = """
Maddy is a friendly and intuitive AI agent designed to help people with low awareness of phishing attacks. 
It analyzes emails and SMS messages to determine whether they are phishing attempts or safe. 
Maddy provides results in three simple outputs:
1. Whether the message is a phishing attempt or safe.
2. A risk score (High, Medium, or Low).
3. Key points explaining how it detected the message as phishing or safe.
"""

# Load frontend HTML
try:
    with open('index.html', 'r') as file:
        html_template = file.read()
except FileNotFoundError:
    html_template = "<h1>Error: index.html not found</h1>"

# Health check route
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# Root route
@app.route('/')
def home():
    return render_template_string(html_template)

# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        email_text = data.get('email', '').strip()

        if not email_text:
            return jsonify({'error': 'No email provided'}), 400

        prompt = f"""
        {backstory}

        Analyze the following email/SMS:

        {email_text}

        Provide the result in three parts:
        1. State whether the message is a phishing attempt or safe (use ** for bold).
        2. Provide a risk score (High, Medium, or Low) (use ** for bold).
        3. List points explaining how Maddy detected the message as phishing or safe (e.g., suspicious links, urgent tone, sender mismatch, etc.) (use ** for bold and * for italic).
        """

        # Generate response
        response = model.generate_content(prompt)
        result_text = response.text

        # Convert Markdown to HTML
        result_html = markdown.markdown(result_text)

        # Parse prediction
        prediction = 'Phishing' if 'phishing attempt' in result_text.lower() else 'Safe'

        return jsonify({
            'prediction': prediction,
            'result': result_html
        })
    except genai.GenerationError as e:
        return jsonify({'error': f"API generation error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500

# Vercel compatibility
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')
application = app  # Export for Vercel