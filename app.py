import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from resume_processing.text_extractor import extract_text
from resume_processing.nlp_processor import process_resume_sections
from resume_processing.ats_scorer import calculate_ats_score
from resume_processing.grammar_checker import check_grammar_and_spelling

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'doc', 'txt'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_resume():
    """Main route for resume upload and analysis."""
    if request.method == 'POST':
        # Check if file is present
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        resume_file = request.files['resume']
        
        # Check if filename is empty
        if resume_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Validate file type
        if resume_file and allowed_file(resume_file.filename):
            # Secure the filename
            filename = secure_filename(resume_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(filepath)
            
            try:
                # Extract text from the resume
                resume_text = extract_text(filepath)
                
                # Process resume sections
                resume_sections = process_resume_sections(resume_text)
                
                # Check grammar and spelling
                grammar_checks = check_grammar_and_spelling(resume_text)
                
                # Calculate ATS score
                ats_score = calculate_ats_score(resume_text, resume_sections)
                
                # Remove the uploaded file after processing
                os.remove(filepath)
                
                return jsonify({
                    'sections': resume_sections,
                    'grammar_checks': grammar_checks,
                    'ats_score': ats_score
                })
            
            except Exception as e:
                # Remove the file in case of error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Render upload page for GET requests
    return render_template('index.html')

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Run the application
    app.run(debug=True)