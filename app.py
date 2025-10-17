from flask import Flask, render_template, request, redirect, url_for
import os, subprocess, json, tempfile, shutil

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# --- ROUTES ---

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/selection")
def selection():
    return render_template("selection.html")


@app.route("/camera")
def camera():
    parameter = request.args.get("param")
    if not parameter:
        return redirect(url_for("selection"))
    return render_template("camera.html", parameter=parameter)


@app.route("/results/<parameter>", methods=["POST"])
def results(parameter):
    # Ensure image was uploaded
    if "image" not in request.files:
        return render_template("results.html", error="No image uploaded.")
    
    image_file = request.files["image"]
    if image_file.filename == "":
        return render_template("results.html", error="No image selected.")

    # Save uploaded image
    image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
    image_file.save(image_path)

    # Temporary output dir
    temp_output = tempfile.mkdtemp(dir=OUTPUT_FOLDER)

    # Map parameter to script
    script_map = {
        "eye": "nova_eye.py",
        "palm": "finalpalm.py",
        "nailbed": "nova_nail.py"
    }

    script = script_map.get(parameter)
    if not script or not os.path.exists(script):
        return render_template("results.html", error=f"Invalid parameter: {parameter}")

    # --- Run detection script ---
    try:
        result = subprocess.run(
            ["python3", script, image_path, temp_output],
            capture_output=True,
            text=True,
            timeout=120
        )
        output_text = result.stdout.strip()
        print("=== SCRIPT OUTPUT ===")
        print(output_text)
        print("=====================")

        try:
            data = json.loads(output_text)
        except json.JSONDecodeError:
            data = {"error": f"Script returned invalid output: {output_text[:200]}"}

    except Exception as e:
        data = {"error": str(e)}

    # --- Prepare display values ---
    annotated_image = None
    zip_file = None
    num_detections = None

    if "error" in data:
        return render_template("results.html", error=data["error"])

    # Copy files to static for display
    if "annotated_image" in data and os.path.exists(data["annotated_image"]):
        dest_path = os.path.join("output", os.path.basename(data["annotated_image"]))
        shutil.copy(data["annotated_image"], os.path.join("static", dest_path))
        annotated_image = dest_path

    if "zip_file" in data and os.path.exists(data["zip_file"]):
        dest_zip = os.path.join("output", os.path.basename(data["zip_file"]))
        shutil.copy(data["zip_file"], os.path.join("static", dest_zip))
        zip_file = dest_zip

    num_detections = (
        data.get("num_eyes") or 
        data.get("num_palms") or 
        data.get("num_nails") or 
        0
    )

    return render_template(
        "results.html",
        annotated_image=annotated_image,
        zip_file=zip_file,
        num_eyes=num_detections,
        parameter=parameter
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
