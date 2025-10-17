# finalpalm.py
# -*- coding: utf-8 -*-
"""
NOVA Palm Detection - Pipeline Compatible (Unified Output)
"""

import sys, os, json, cv2, zipfile
from roboflow import Roboflow
from contextlib import redirect_stdout
import io

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python finalpalm.py <image_path> [output_dir]"}))
        return

    image_path = sys.argv[1]
    output_dir = "static/output/palm"
    os.makedirs(output_dir, exist_ok=True)
    annotated_path = os.path.join(output_dir, f"annotated_{os.path.basename(image_path)}")

    if not os.path.exists(image_path):
        print(json.dumps({"error": f"File not found: {image_path}"}))
        return

    # === Connect to Roboflow (Suppress internal logs) ===
    log_buffer = io.StringIO()
    with redirect_stdout(log_buffer):
        rf = Roboflow(api_key="MCkkLOGQRolmK9RTlG6W")
        project = rf.workspace().project("palmprint-edlc1")
        model = project.version(1).model
        prediction_json = model.predict(image_path, confidence=40, overlap=30).json()

    predictions = prediction_json.get("predictions", [])
    palm_predictions = [p for p in predictions if p.get("class") == "palmcenter"]

    # === Draw and annotate ===
    orig = cv2.imread(image_path)
    annotated = orig.copy()

    for pred in palm_predictions:
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        x1, y1, x2, y2 = x - w//2, y - h//2, x + w//2, y + h//2
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(annotated, f"palmcenter {round(pred['confidence']*100,1)}%",
                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    annotated_path = os.path.join(output_dir, f"annotated_{os.path.basename(image_path)}")
    cv2.imwrite(annotated_path, annotated)

    # === Crop and save ===
    crop_dir = os.path.join(output_dir, "crops")
    os.makedirs(crop_dir, exist_ok=True)
    saved_crops = []

    for i, pred in enumerate(palm_predictions):
        x, y, w, h = int(pred["x"]), int(pred["y"]), int(pred["width"]), int(pred["height"])
        x1, y1, x2, y2 = x - w//2, y - h//2, x + w//2, y + h//2
        crop = orig[y1:y2, x1:x2]
        if crop.size > 0:
            crop_path = os.path.join(crop_dir, f"crop_{i}_palmcenter.jpg")
            cv2.imwrite(crop_path, crop)
            saved_crops.append(crop_path)

    # === Zip all cropped palms ===
    zip_filename = os.path.join(output_dir, "palm_crops.zip")
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for root, _, files_in_dir in os.walk(crop_dir):
            for file in files_in_dir:
                zipf.write(os.path.join(root, file))

    # === Output JSON for pipeline ===
    output = {
        "image": image_path,
        "annotated_image": annotated_path,
        "num_palms": len(palm_predictions),
        "saved_palms": saved_crops,
        "zip_file": zip_filename
    }

    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    main()
