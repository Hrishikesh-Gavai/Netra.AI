import os
import logging
import numpy as np
import webbrowser
from flask import Flask, render_template, request, session, jsonify, redirect
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import google.generativeai as genai
from web_scraper import search_eye_doctors_by_city

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'

# ==================== GEMINI API CONFIGURATION ====================
GEMINI_API_KEY = "AIzaSyAWznP_b6ozWlWklpCjYwF03O2R34UmGxw"
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "models/gemini-2.5-flash"

def generate_gemini_content(disease, confidence):
    """Generate educational content using Gemini API"""
    try:
        model_gemini = genai.GenerativeModel(GEMINI_MODEL)
        prompt = f"""As an eye health AI assistant, provide a concise, patient-friendly response about {disease} (detected with {confidence:.1f}% confidence).

Please provide EXACTLY in this JSON format without any markdown formatting:
{{
  "description": "A plain-language explanation of what this condition is (1-2 sentences).",
  "symptoms": "Common symptoms patients might notice (1 sentence).",
  "risk_factors": "Main risk factors for developing this condition (1 sentence).",
  "next_steps": "Recommended next steps and when to see a doctor (1-2 sentences).",
  "lifestyle_tips": "2-3 specific lifestyle recommendations or preventive measures. Use bullet points with • symbol."
}}

Keep the response concise and medically accurate but reassuring."""
        response = model_gemini.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        result = json.loads(response_text.strip())
        return result
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        return get_fallback_content(disease)

def get_fallback_content(disease):
    """Fallback educational content when Gemini is unavailable"""
    content_map = {
        'Cataract': {
            'description': 'A cataract is a clouding of the eye\'s natural lens. It develops gradually with age.',
            'symptoms': 'Blurred vision, glare at night, faded colors.',
            'risk_factors': 'Age, diabetes, smoking, UV exposure.',
            'next_steps': 'Consult an ophthalmologist. Surgery is safe and effective.',
            'lifestyle_tips': '• Wear UV sunglasses\n• Quit smoking\n• Eat antioxidant-rich foods'
        },
        'Diabetic Retinopathy': {
            'description': 'Diabetes complication damaging retina blood vessels.',
            'symptoms': 'Floaters, blurred vision, vision loss.',
            'risk_factors': 'Poor blood sugar control, high BP, long-term diabetes.',
            'next_steps': 'Tight glycemic control and annual eye exams.',
            'lifestyle_tips': '• Monitor HbA1c\n• Control BP\n• Get dilated eye exam yearly'
        },
        'Glaucoma': {
            'description': 'Optic nerve damage often due to high eye pressure.',
            'symptoms': 'Gradual peripheral vision loss.',
            'risk_factors': 'Age >60, family history, high eye pressure.',
            'next_steps': 'Immediate ophthalmology visit. Eye drops or surgery.',
            'lifestyle_tips': '• Take drops regularly\n• Exercise\n• Avoid eye pressure spikes'
        },
        'Normal': {
            'description': 'Your retinal scan appears healthy.',
            'symptoms': 'No concerning symptoms.',
            'risk_factors': 'Age, family history, diabetes.',
            'next_steps': 'Regular checkups every 1-2 years.',
            'lifestyle_tips': '• 20-20-20 rule for screens\n• UV protection\n• Balanced diet'
        }
    }
    return content_map.get(disease, content_map['Normal'])

# Load TensorFlow model
MODEL_PATH = "models/eye_disease_model.h5"

def load_model_compatible(model_path):
    try:
        import tensorflow as tf
        from tensorflow.keras.models import load_model
        try:
            model = load_model(model_path, compile=False)
            logging.info("Model loaded with compile=False")
            return model
        except Exception as e1:
            logging.warning(f"First attempt failed: {e1}")
            try:
                from tensorflow.keras.layers import InputLayer
                custom_objects = {'InputLayer': InputLayer}
                model = load_model(model_path, custom_objects=custom_objects, compile=False)
                logging.info("Model loaded with custom objects")
                return model
            except Exception as e2:
                logging.warning(f"Second attempt failed: {e2}")
                try:
                    tf.compat.v1.disable_eager_execution()
                    model = load_model(model_path, compile=False)
                    logging.info("Model loaded with legacy mode")
                    return model
                except Exception as e3:
                    logging.error(f"All loading attempts failed: {e3}")
                    raise
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        return None

logging.info(f"Loading model from {MODEL_PATH}...")
model = load_model_compatible(MODEL_PATH)
if model is None:
    logging.error("Could not load model. Please retrain the model.")
    # We'll still start the app but prediction will fail
else:
    logging.info("Model loaded successfully!")

CATEGORIES = ["Cataract", "Diabetic Retinopathy", "Glaucoma", "Normal"]
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Model evaluation metrics
MODEL_METRICS = {
    'accuracy': 73.96,
    'error_rate': 26.04,
    'per_class': {
        'Cataract': {'precision': 92.86, 'recall': 75.36, 'f1': 83.20},
        'Diabetic Retinopathy': {'precision': 96.48, 'recall': 100.00, 'f1': 98.21},
        'Glaucoma': {'precision': 67.06, 'recall': 28.36, 'f1': 39.86},
        'Normal': {'precision': 52.63, 'recall': 88.79, 'f1': 66.09}
    },
    'weighted': {'precision': 77.40, 'recall': 73.96, 'f1': 72.39},
}

TEAM_MEMBERS = [
    {'name': 'Hrishikesh Gavai', 'role': 'Full Stack Developer & Model Trainer', 'image': '/assets/Eclipse.png', 'bio': 'Leading the development of Netra.AI and training deep learning models.'},
    {'name': 'Deepak Warude', 'role': 'Dataset Curator & Model Evaluator', 'image': '/assets/Eclipse.png', 'bio': 'Curating retinal image datasets and evaluating model performance.'},
    {'name': 'Atharva Ghayal', 'role': 'Testing Specialist', 'image': '/assets/Eclipse.png', 'bio': 'Ensuring system reliability across various image conditions.'},
    {'name': 'Tejas Sangle', 'role': 'Model Architect & Performance Analyst', 'image': '/assets/Eclipse.png', 'bio': 'Designing neural network architecture and analyzing model performance.'}
]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", team_members=TEAM_MEMBERS)

@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded properly'}), 500
    if "file" not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({'error': 'No file selected'}), 400
    if file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(f"{timestamp}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        from tensorflow.keras.preprocessing import image
        img = image.load_img(filepath, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        prediction = model.predict(img_array)
        result = CATEGORIES[np.argmax(prediction)]
        confidence = float(np.max(prediction) * 100)
        probabilities = {}
        for i, category in enumerate(CATEGORIES):
            probabilities[category] = float(prediction[0][i] * 100)
        
        logging.info(f"Prediction: {result} (Confidence: {confidence:.2f}%)")
        gemini_content = generate_gemini_content(result, confidence)
        
        session['prediction_result'] = {
            'disease': result,
            'confidence': confidence,
            'probabilities': probabilities,
            'image_path': filepath,
            'gemini_content': gemini_content
        }
        return jsonify({'success': True, 'redirect': '/loading'})

@app.route("/loading")
def loading():
    return render_template("loading.html")

@app.route("/results")
def results():
    prediction_result = session.get('prediction_result', None)
    if not prediction_result:
        return redirect('/')
    prediction_data = {
        'result': prediction_result['disease'],
        'confidence': f"{prediction_result['confidence']:.1f}%",
        'probabilities': prediction_result['probabilities'],
        'img_path': prediction_result['image_path'],
        'metrics': {
            'accuracy': MODEL_METRICS['accuracy'],
            'error_rate': MODEL_METRICS['error_rate'],
            'weighted': MODEL_METRICS['weighted'],
            'per_class': MODEL_METRICS['per_class']
        },
        'gemini': prediction_result.get('gemini_content', get_fallback_content(prediction_result['disease']))
    }
    return render_template("result.html", prediction_data=prediction_data)

@app.route("/api/metrics")
def get_metrics():
    return jsonify(MODEL_METRICS)

@app.route("/api/search-doctors", methods=["GET"])
def search_doctors_by_city():
    city = request.args.get('city', '')
    if not city:
        return jsonify({'success': False, 'error': 'City name required'}), 400
    try:
        results = search_eye_doctors_by_city(city)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logging.error(f"Doctor search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/doctors")
def doctors():
    return render_template("doctors.html")

if __name__ == "__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        webbrowser.open("http://127.0.0.1:5000")
        print("\n" + "="*50)
        print("🌐 Opening browser at http://127.0.0.1:5000")
        print("="*50 + "\n")
    print("👁️  Eye Disease Detection System is starting...")
    print("⚡ Press CTRL+C to stop the server\n")
    app.run(debug=True, host="127.0.0.1", port=5000)