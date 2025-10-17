from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import subprocess, json, os, tempfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/camera/<scan_type>')
def camera(scan_type):
    return render_template('camera.html', scan_type=scan_type.capitalize())

@app.route('/upload/<scan_type>', methods=['POST'])
def upload(scan_type):
    if 'image' not in request.files:
        return "No image uploaded", 400

    file = request.files['image']
    if file.filename == '':
        return "No file selected", 400

    # Save uploaded image
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Run the correct detection script
    if scan_type == "eye":
        cmd = ["python3", "nova_eye.py", filepath]
    elif scan_type == "palm":
        cmd = ["python3", "finalpalm.py", filepath]
    elif scan_type == "nail":
        cmd = ["python3", "nova_nail.py", filepath]
    else:
        return "Invalid scan type", 400

    # Execute the script
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = json.loads(result.stdout)
    except Exception as e:
        return jsonify({"error": str(e), "details": result.stderr if 'result' in locals() else None}), 500

    return render_template('results.html', result=output, scan_type=scan_type.capitalize())

@app.route('/download/<path:filename>')
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
