import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import spacy
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Load the spaCy language model
nlp = spacy.load("en_core_web_sm")

def extract_skills_from_text(text):
    """
    Extract skills from resume text using spaCy
    """
    # Predefined list of common skills
    common_skills = [
        "python", "java", "c++", "javascript", "react", "angular", "vue", 
        "machine learning", "data science", "web development", "mobile development", 
        "cloud computing", "aws", "azure", "gcp", "sql", "database", "tensorflow", 
        "keras", "django", "flask", "nodejs", "git", "docker", "kubernetes", 
        "agile", "scrum", "communication", "leadership", "problem solving"
    ]
    
    # Convert text to lowercase for easier matching
    text_lower = text.lower()
    
    # Find skills that appear in the text
    found_skills = [skill for skill in common_skills if skill in text_lower]
    
    return ", ".join(set(found_skills))

def calculate_resume_score(skills):
    """
    Calculate a basic score based on the number of skills
    """
    skill_count = len(skills.split(",")) if skills else 0
    
    # Score ranges from 0-100
    if skill_count < 3:
        return "30"
    elif skill_count < 5:
        return "60"
    elif skill_count < 7:
        return "80"
    else:
        return "95"

def download_pdf(url):
    """
    Download PDF from URL
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save the PDF temporarily
        with open("temp_resume.pdf", "wb") as f:
            f.write(response.content)
        
        return "temp_resume.pdf"
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF
    """
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""

@app.route("/analyzeResume", methods=["POST", "OPTIONS"])
def analyze_resume():
    """
    Endpoint to analyze resume with CORS support
    """
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = jsonify({"message": "Preflight request successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Log incoming request details
        logger.info(f"Received request: {request.json}")
        
        # Get the resume URL from the request
        data = request.get_json()
        resume_url = data.get("resumeUrl")
        
        if not resume_url:
            logger.error("No resume URL provided")
            return jsonify({"error": "No resume URL provided"}), 400
        
        # Download PDF
        pdf_path = download_pdf(resume_url)
        
        if not pdf_path:
            logger.error("Failed to download resume")
            return jsonify({"error": "Failed to download resume"}), 500
        
        # Extract text
        resume_text = extract_text_from_pdf(pdf_path)
        
        # Clean up temporary file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Extract skills
        skills = extract_skills_from_text(resume_text)
        
        # Calculate score
        score = calculate_resume_score(skills)
        
        # Prepare response with CORS headers
        response = jsonify({
            "skills": skills,
            "score": score
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        response = jsonify({"error": "Internal server error", "details": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({"status": "healthy", "message": "Resume Analysis API is running"})

if __name__ == "__main__":
    app.run(debug=True)