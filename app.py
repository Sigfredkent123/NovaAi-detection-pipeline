from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess, json, os

app = Flask(__name__)

# Use static folders for uploads and outputs
UPLOAD_FOLDER = os.path.join("static", "uploads")
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

    # Map scan_type to script
    scripts = {
        "eye": "nova_eye.py",
        "palm": "finalpalm.py",
        "nail": "nova_nail.py"
    }

    if scan_type not in scripts:
        return "Invalid scan type", 400

    cmd = ["python3", scripts[scan_type], filepath]

    # Run detection script
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        output = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Detection script timed out"}), 500
    except Exception as e:
        return jsonify({
            "error": str(e),
            "details": result.stderr if 'result' in locals() else None
        }), 500

    # Convert local paths to URLs
    if "annotated_image" in output:
        output["annotated_image"] = "/" + output["annotated_image"].replace("\\", "/")
    if "zip_file" in output:
        output["zip_file"] = "/" + output["zip_file"].replace("\\", "/")
    for key in ["saved_eyes", "saved_palms", "saved_nails"]:
        if key in output:
            output[key] = ["/" + f.replace("\\", "/") for f in output[key]]

    return render_template('results.html', result=output, scan_type=scan_type.capitalize())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
