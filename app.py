import os
import json
import logging
import math
import requests
import time
import pymupdf  # PyMuPDF
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from google import genai
from google.genai import types
from ai_job_agent import search_web_for_jobs

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
logging.basicConfig(level=logging.INFO)

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY not found in environment variables.")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = 'gemini-3.6-flash'

# Initialize Database
db_url = os.getenv('DATABASE_URL', 'sqlite:///jobs.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class LocationCache(db.Model):
    __tablename__ = 'location_cache'
    location_name = db.Column(db.String, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String)
    company = db.Column(db.String)
    location = db.Column(db.String)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    description = db.Column(db.Text)
    job_url = db.Column(db.String)
    site = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class ExclusiveJob(db.Model):
    __tablename__ = 'exclusive_jobs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String)
    logo_url = db.Column(db.String)
    badge_color = db.Column(db.String)
    badge_text = db.Column(db.String)
    location = db.Column(db.String)
    type = db.Column(db.String)
    status = db.Column(db.String, default='Draft')
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

with app.app_context():
    db.create_all()

def get_cached_location(location_name):
    loc = LocationCache.query.filter_by(location_name=location_name.lower()).first()
    if loc:
        return loc.latitude, loc.longitude
    return None

def cache_location(location_name, lat, lon):
    loc = LocationCache.query.filter_by(location_name=location_name.lower()).first()
    if loc:
        loc.latitude = lat
        loc.longitude = lon
    else:
        loc = LocationCache(location_name=location_name.lower(), latitude=lat, longitude=lon)
        db.session.add(loc)
    db.session.commit()

def geocode_location(location_name):
    if not location_name or location_name.lower() in ['remote', 'anywhere']:
        return None, None
    cached = get_cached_location(location_name)
    if cached:
        return cached[0], cached[1]
    
    try:
        # Use Photon API
        url = f"https://photon.komoot.io/api/?q={requests.utils.quote(location_name)}&limit=1"
        headers = {"User-Agent": "NareshITJobAgent/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('features') and len(data['features']) > 0:
                coords = data['features'][0]['geometry']['coordinates']
                lon, lat = coords[0], coords[1]
                cache_location(location_name, lat, lon)
                return lat, lon
    except Exception as e:
        logging.error(f"Geocoding failed for {location_name}: {e}")
    return None, None

def haversine(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return None
    R = 6371  # Radius of earth in kilometers.
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return round(distance, 1)


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def page_not_found(e):
    return send_from_directory(app.static_folder, '404.html'), 404


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "gemini_configured": client is not None})


@app.route('/api/generate-resume', methods=['POST'])
def generate_resume():
    if not client:
        return jsonify({"error": "Gemini API key is not configured"}), 500

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    prompt = f"""
    You are an expert ATS resume writer and career coach. Your task is to process the following student details and format them into an ATS-friendly resume.
    
    CRITICAL RULES:
    1. NEVER fabricate or invent companies, job titles, degrees, certifications, skills, projects, metrics, or achievements.
    2. If the student has no professional experience, DO NOT invent experience. Focus solely on their projects, education, certifications, and skills.
    3. Understand the student's actual information and improve the wording for ATS readability.
    4. Create a compelling, truthful professional summary based ONLY on provided details.
    5. Improve project descriptions and experience bullet points (if any) to highlight actions and outcomes without adding fake metrics.
    6. Organize skills logically.

    Student Information:
    {json.dumps(data, indent=2)}

    Please return a structured JSON response EXACTLY matching this schema:
    {{
        "professional_summary": "string",
        "skills": {{ "technical": "string", "soft": "string" }},
        "projects": [ {{ "name": "string", "technologies": "string", "bullet_points": ["string"] }} ],
        "experience": [ {{ "company": "string", "role": "string", "duration": "string", "bullet_points": ["string"] }} ],
        "education": {{ "degree": "string", "college": "string", "graduation_year": "string" }},
        "certifications": ["string"]
    }}
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
        
        # Merge back personal info
        result['personal_info'] = data.get('personal_info', {})
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error calling Gemini: {e}")
        return jsonify({"error": "Failed to generate resume"}), 500


@app.route('/api/search-jobs', methods=['POST'])
def search_jobs():
    data = request.json
    role = data.get('role', 'Software Engineer')
    location = data.get('location', 'India')
    results_wanted = int(data.get('results', 10))
    user_lat = data.get('latitude')
    user_lon = data.get('longitude')
    radius = data.get('radius') # in km

    try:
        # Determine Search Center
        search_center_lat, search_center_lon = None, None
        search_center_display = location
        search_location_name = location
        
        if user_lat is not None and user_lon is not None:
            search_center_lat, search_center_lon = float(user_lat), float(user_lon)
            search_center_display = "My GPS Location"
            
            # If the text is "My Location" or empty, we need a real name for the text-based search
            if not location or location.lower() == "my location":
                try:
                    rev_url = f"https://photon.komoot.io/reverse?lon={search_center_lon}&lat={search_center_lat}"
                    headers = {"User-Agent": "NareshITJobAgent/1.0"}
                    rev_res = requests.get(rev_url, headers=headers, timeout=5)
                    if rev_res.status_code == 200:
                        props = rev_res.json().get('features', [{}])[0].get('properties', {})
                        # Try to get the most specific location name
                        search_location_name = props.get('city') or props.get('county') or props.get('state') or "India"
                    else:
                        search_location_name = "India"
                except Exception as e:
                    logging.error(f"Reverse geocoding failed: {e}")
                    search_location_name = "India"
        else:
            search_center_lat, search_center_lon = geocode_location(location)

        jobs_list = search_web_for_jobs(
            role=role,
            location=search_location_name,
            results_wanted=results_wanted
        )
        
        def safe_str(val, limit=None):
            if val is None or (isinstance(val, float) and math.isnan(val)):
                return ""
            s = str(val)
            if limit and len(s) > limit:
                return s[:limit] + "..."
            return s
            
        normalized_jobs = []
        counts = {"total": 0, "mapped": 0, "remote": 0, "unmapped": 0}

        countries = ["india", "united states", "usa", "uk", "canada", "australia", "germany", "singapore", "vietnam"]

        for job in jobs_list:
            job_title = safe_str(job.get('title'))
            job_company = safe_str(job.get('company'))
            job_location = safe_str(job.get('location'))
            job_url = safe_str(job.get('job_url'))
            job_desc = safe_str(job.get('description'), 500)
            
            # Deduplication key (very basic)
            if any(j['title'] == job_title and j['company'] == job_company for j in normalized_jobs):
                continue
                
            # Determine location_type
            loc_lower = job_location.lower()
            location_type = "onsite"
            if "remote" in loc_lower or "work from home" in loc_lower or "worldwide" in loc_lower:
                location_type = "remote"
            elif "hybrid" in loc_lower:
                location_type = "hybrid"
            elif loc_lower in countries:
                location_type = "unknown"

            # Geocode
            lat, lon = None, None
            if location_type not in ["remote", "unknown"]:
                lat, lon = geocode_location(job_location)
                if lat is not None and lon is not None:
                    import random
                    # Add a tiny jitter (approx 500m-2km) so pins don't perfectly stack
                    lat += random.uniform(-0.015, 0.015)
                    lon += random.uniform(-0.015, 0.015)
                
            distance_km = None
            if search_center_lat is not None and search_center_lon is not None and lat is not None and lon is not None:
                distance_km = haversine(search_center_lat, search_center_lon, lat, lon)
                
            # Filter by radius if provided
            # if radius and radius != "Anywhere" and search_center_lat is not None and search_center_lon is not None:
            #     if location_type == "remote":
            #         continue # Exclude remote from strict local radius search
            #     if distance_km is not None and distance_km > float(radius):
            #         continue # Exclude out of bounds

            counts["total"] += 1
            if location_type == "remote":
                counts["remote"] += 1
            elif lat is not None and lon is not None:
                counts["mapped"] += 1
            else:
                counts["unmapped"] += 1

            normalized_jobs.append({
                "id": f"{job_company}-{job_title}".replace(" ", "-").lower(),
                "title": job_title,
                "company": job_company,
                "location": job_location,
                "location_type": location_type,
                "latitude": lat,
                "longitude": lon,
                "distance_km": distance_km,
                "description": job_desc,
                "job_url": job_url,
                "site": safe_str(job.get('site'))
            })

        return jsonify({
            "search_center": {
                "latitude": search_center_lat,
                "longitude": search_center_lon,
                "display_name": search_center_display
            },
            "jobs": normalized_jobs,
            "counts": counts
        })
    except Exception as e:
        logging.error(f"Error searching jobs: {e}")
        return jsonify({"error": "Failed to search jobs"}), 500

@app.route('/api/geocode', methods=['POST'])
def api_geocode():
    data = request.json
    location = data.get('location')
    if not location:
        return jsonify({"error": "Location is required"}), 400
    
    lat, lon = geocode_location(location)
    if lat is not None and lon is not None:
        return jsonify({"latitude": lat, "longitude": lon})
    return jsonify({"error": "Could not geocode location"}), 404

@app.route('/api/match-job', methods=['POST'])
def match_job():
    if not client:
        return jsonify({"error": "Gemini API key is not configured"}), 500

    data = request.json
    profile = data.get('profile', '')
    job = data.get('job', {})

    if not profile or not job:
        return jsonify({"error": "Profile and job data are required"}), 400

    prompt = f"""
    You are an expert AI recruitment agent. Compare the following Student Profile against the Job Description.
    
    You must analyze:
    - Required skills vs. student's technical stack
    - Preferred skills
    - Experience level
    - Education
    - Location match
    - Projects and their relevance

    Use a transparent and realistic scoring approach. Do not pretend that the score is an official ATS score; it is an AI readiness estimate.

    Student Profile:
    {json.dumps(profile, indent=2)}
    
    Job Details:
    {json.dumps(job, indent=2)}

    Return exactly a structured JSON response EXACTLY matching this schema:
    {{
        "match_score": 0,
        "matched_skills": ["string"],
        "missing_skills": ["string"],
        "strengths": ["string"],
        "concerns": ["string"],
        "reason": "string"
    }}
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return jsonify(json.loads(response.text))
    except Exception as e:
        logging.error(f"Error matching job: {e}")
        return jsonify({"error": "Failed to match job"}), 500

@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    if not client:
        return jsonify({"error": "Gemini API key is not configured"}), 500

    data = request.json
    profile = data.get('profile', '')
    job = data.get('job', {})

    if not profile or not job:
        return jsonify({"error": "Profile and job data are required"}), 400

    prompt = f"""
    You are an expert AI career coach and recruiter. Your objective is to produce a personalized, 
    highly compelling cover letter that highlights the candidate's qualifications for a specific job.
    
    CRITICAL INSTRUCTIONS:
    - You must write the cover letter from the perspective of the candidate.
    - Tailor the letter specifically to the company and the job role.
    - Highlight the candidate's most relevant skills and projects based on the Job Description.
    - Maintain a professional, confident, and enthusiastic tone.
    - The output must be valid Markdown. DO NOT wrap the output in a JSON object, just return the raw Markdown string.
    - DO NOT include placeholders like [Your Name] if the student's name is available in the profile.
    
    Candidate Profile (Resume Data):
    {json.dumps(profile, indent=2)}
    
    Job Description:
    {json.dumps(job, indent=2)}
    """

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return jsonify({"cover_letter": response.text})
    except Exception as e:
        logging.error(f"Error generating cover letter: {e}")
        return jsonify({"error": "Failed to generate cover letter"}), 500


@app.route('/api/analyze-resume', methods=['POST'])
def analyze_resume():
    if not client:
        return jsonify({"error": "Gemini API key is not configured"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    job_description = request.form.get('job_description', '')

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400

    try:
        # Read PDF using PyMuPDF
        pdf_bytes = file.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
            
        if not text.strip():
            return jsonify({"error": "Could not extract text from PDF"}), 400

        prompt = f"""
        You are an expert ATS system and career coach. Analyze the following Resume Text against the provided Job Description.
        
        CRITICAL RULES:
        1. Prioritize truthful optimization over keyword stuffing.
        2. Make the output concise and highly useful for the candidate.
        3. Do not guarantee an official ATS score, but provide a realistic readiness estimate (0-100).
        
        Resume Text:
        {text}
        
        Job Description:
        {job_description}
        
        Provide a detailed JSON response EXACTLY matching this schema:
        {{
            "ats_readiness_score": 0,
            "keyword_match": ["string"],
            "missing_keywords": ["string"],
            "strengths": ["string"],
            "weaknesses": ["string"],
            "recommendations": ["string"],
            "resume_improvements": ["string"]
        }}
        """

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return jsonify(json.loads(response.text))

    except Exception as e:
        logging.error(f"Error parsing PDF or calling Gemini: {e}")
        return jsonify({"error": "Failed to analyze resume"}), 500



# ================= EXCLUSIVE JOBS API =================

@app.route('/admin')
def admin_page():
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/api/exclusive-jobs', methods=['GET'])
def get_exclusive_jobs():
    status_filter = request.args.get('status')
    if status_filter:
        jobs = ExclusiveJob.query.filter_by(status=status_filter).order_by(ExclusiveJob.id.desc()).all()
    else:
        jobs = ExclusiveJob.query.order_by(ExclusiveJob.id.desc()).all()
        
    job_list = []
    for j in jobs:
        job_list.append({
            'id': j.id,
            'title': j.title,
            'description': j.description,
            'link': j.link,
            'logo_url': j.logo_url,
            'badge_color': j.badge_color,
            'badge_text': j.badge_text,
            'location': j.location,
            'type': j.type,
            'status': j.status,
            'created_at': j.created_at
        })
    return jsonify(job_list)

@app.route('/api/exclusive-jobs', methods=['POST'])
def create_exclusive_job():
    data = request.json
    new_job = ExclusiveJob(
        title=data.get('title'),
        description=data.get('description'),
        link=data.get('link'),
        logo_url=data.get('logoUrl'),
        badge_color=data.get('badgeColor'),
        badge_text=data.get('badgeText'),
        location=data.get('location'),
        type=data.get('type'),
        status=data.get('status', 'Draft')
    )
    db.session.add(new_job)
    db.session.commit()
    return jsonify({"success": True, "id": new_job.id})

@app.route('/api/exclusive-jobs/<int:job_id>', methods=['PUT'])
def update_exclusive_job(job_id):
    data = request.json
    job = ExclusiveJob.query.get(job_id)
    if job:
        job.title = data.get('title', job.title)
        job.description = data.get('description', job.description)
        job.link = data.get('link', job.link)
        job.logo_url = data.get('logoUrl', job.logo_url)
        job.badge_color = data.get('badgeColor', job.badge_color)
        job.badge_text = data.get('badgeText', job.badge_text)
        job.location = data.get('location', job.location)
        job.type = data.get('type', job.type)
        job.status = data.get('status', job.status)
        db.session.commit()
    return jsonify({"success": True})

@app.route('/api/exclusive-jobs/<int:job_id>', methods=['DELETE'])
def delete_exclusive_job(job_id):
    job = ExclusiveJob.query.get(job_id)
    if job:
        db.session.delete(job)
        db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':

    app.run(debug=True, port=5000)
