# nova_eye.py
# -*- coding: utf-8 -*-
"""
NOVA Eye Detection - Flask-Compatible Pipeline
"""

import sys, os, json, zipfile
from PIL import Image, ImageDraw, ImageFont
from inference_sdk import InferenceHTTPClient

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python nova_eye.py <image_path> [output_dir]"}))
        return

    image_path = sys.argv[1]
    output_dir = os.path.join("static", "output", "eye")
    os.makedirs(output_dir, exist_ok=True)
    annotated_path = os.path.join(output_dir, f"annotated_{os.path.basename(image_path)}")

    if not os.path.exists(image_path):
        print(json.dumps({"error": f"File not found: {image_path}"}))
        return

    # Connect to Roboflow Workflow
    client = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key="rXklt59qJc3uGQUVi7iZ"  # Your valid API key
    )

    try:
        result = client.run_workflow(
            workspace_name="newnova-mkn50",
            workflow_id="custom-workflow-2",
            images={"image": image_path},
            use_cache=True
        )
        predictions = result[0]["predictions"]["predictions"]
    except Exception as e:
        print(json.dumps({"error": f"Workflow failed: {str(e)}"}))
        return

    # Annotate detections
    annotated_path = os.path.join(output_dir, f"annotated_{os.path.basename(image_path)}")
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    for pred in predictions:
        x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
        cls = pred["class"]
        conf = pred.get("confidence", 1.0)
        x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        draw.rectangle([x0, y0, x1, y1], outline="red", width=3)
        draw.text((x0, y0 - 10), f"{cls} {conf:.2f}", fill="red", font=font)
    image.save(annotated_path)

    # Save crops
    crop_dir = os.path.join(output_dir, "crops")
    os.makedirs(crop_dir, exist_ok=True)
    orig = Image.open(image_path).convert("RGB")
    saved_crops = []

    for i, pred in enumerate(predictions):
        x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
        cls = pred["class"]
        x0, y0, x1, y1 = int(x - w / 2), int(y - h / 2), int(x + w / 2), int(y + h / 2)
        crop = orig.crop((x0, y0, x1, y1))
        crop_path = os.path.join(crop_dir, f"crop_{i}_{cls}.png")
        crop.save(crop_path)
        saved_crops.append(crop_path)

    # Zip crops
    zip_filename = os.path.join(output_dir, "eye_crops.zip")
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for root, _, files in os.walk(crop_dir):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    # Output JSON
    output = {
        "image": image_path,
        "annotated_image": annotated_path,
        "num_eyes": len(predictions),
        "saved_eyes": saved_crops,
        "zip_file": zip_filename
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
