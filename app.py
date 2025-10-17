from flask import Flask, render_template, request, send_file
import subprocess, json, os, tempfile

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "image" not in request.files:
            return "No file part", 400
        file = request.files["image"]
        if file.filename == "":
            return "No selected file", 400

        # Save uploaded file
        tmp_dir = tempfile.mkdtemp()
        image_path = os.path.join(tmp_dir, file.filename)
        file.save(image_path)

        # Run the detection pipeline
        try:
            result = subprocess.run(
                ["python", "nova_eye.py", image_path],
                capture_output=True, text=True, check=True
            )
            data = json.loads(result.stdout)
            annotated_path = data.get("annotated_image")
            if not annotated_path or not os.path.exists(annotated_path):
                return "Detection failed.", 500
            return send_file(annotated_path, mimetype="image/png")
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}", 500
        except Exception as e:
            return f"Error: {e}", 500

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
