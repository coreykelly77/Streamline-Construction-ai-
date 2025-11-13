from flask import Flask, request, jsonify

import openai

import pdfplumber

import json

import os



# Initialize Flask app

app = Flask(__name__)



# Load API key from environment variable (Render setup will handle this)

openai.api_key = os.getenv("OPENAI_API_KEY")



@app.route('/')

def home():

    return "✅ Streamline Construction AI Backend is running!"



@app.route('/api/estimate', methods=['POST'])

def estimate():

    try:

        # Check for uploaded file

        if 'file' not in request.files:

            return jsonify({"error": "No file uploaded"}), 400



        file = request.files['file']



        # Ensure the file is a PDF

        if not file.filename.lower().endswith('.pdf'):

            return jsonify({"error": "Please upload a PDF file"}), 400



        # Extract text from PDF

        with pdfplumber.open(file) as pdf:

            text = ""

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:

                    text += page_text + "\n"



        if not text.strip():

            return jsonify({"error": "No readable text found in the PDF"}), 400



        # Build prompt for AI

        prompt = f"""

        You are a professional construction estimator.

        Analyze the following drawing text and estimate:

        - Concrete (m³)

        - Reinforcement steel (kg)

        - Formwork (m²)

        Respond ONLY with a JSON object. Example:

        {{

          "Concrete": 15.2,

          "Reinforcement": 120.5,

          "Formwork": 42

        }}

        Here is the text:

        {text}

        """



        # Send to OpenAI

        response = openai.ChatCompletion.create(

            model="gpt-4o",

            messages=[{"role": "user", "content": prompt}],

            temperature=0.1

        )



        ai_text = response.choices[0].message.content.strip()



        # Parse AI response into JSON

        try:

            quantities = json.loads(ai_text)

        except json.JSONDecodeError:

            return jsonify({"error": "AI returned unreadable data", "raw_output": ai_text}), 500



        # Apply base cost rates (you can change these)

        rates = {

            "Concrete": 120,        # cost per m³

            "Reinforcement": 2.5,   # cost per kg

            "Formwork": 25          # cost per m²

        }



        cost_summary = {}

        total_cost = 0



        for item, qty in quantities.items():

            unit_cost = rates.get(item, 0)

            total = qty * unit_cost

            total_cost += total

            cost_summary[item] = {

                "Quantity": qty,

                "Unit Cost": unit_cost,

                "Total": round(total, 2)

            }



        result = {

            "quantities": quantities,

            "costs": cost_summary,

            "total_estimate": round(total_cost, 2)

        }



        return jsonify(result)



    except Exception as e:

        return jsonify({"error": str(e)}), 500





if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
