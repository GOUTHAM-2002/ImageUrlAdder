import os
import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Google Custom Search API details (Replace with your actual API key and Search Engine ID)
GOOGLE_API_KEY = "AIzaSyB-GRGg1Kv6rGW1YaaV6wtt_-21lzkgSwQ"
SEARCH_ENGINE_ID = "90c63447a8d884073"


def is_valid_image(url):
    """Checks if the image URL is valid by making a HEAD request."""
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_image_url(name):
    """Fetches a valid image result for a given name using Google Custom Search API."""
    search_url = "https://www.googleapis.com/customsearch/v1"
    for attempt in range(3):  # Try fetching up to 3 images
        params = {
            "q": name,
            "cx": SEARCH_ENGINE_ID,
            "key": GOOGLE_API_KEY,
            "searchType": "image",
            "num": 1,  # Fetch only one image per request to save API costs
            "start": attempt + 1  # Start index for pagination
        }
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                image_url = data["items"][0]["link"]
                if is_valid_image(image_url):
                    return image_url  # Return first valid image
    return "No image found"  # If all attempts fail


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file_ext = os.path.splitext(file.filename)[1].lower()

            # Convert XLSX to CSV if needed
            if file_ext == ".xlsx":
                df = pd.read_excel(file)
                csv_filename = file.filename.rsplit(".", 1)[0] + ".csv"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
                df.to_csv(filepath, index=False)
            else:
                file.save(filepath)
                df = pd.read_csv(filepath)

            # Ensure the CSV has a column named "Item Name"
            if "Item Name" not in df.columns:
                return "CSV must have an 'Item Name' column"

            # Fetch image URLs
            df["Image"] = df["Item Name"].apply(get_image_url)

            # Save the updated CSV
            output_filepath = os.path.join(OUTPUT_FOLDER, "updated_" + os.path.basename(filepath))
            df.to_csv(output_filepath, index=False)

            return redirect(url_for("download_file", filename="updated_" + os.path.basename(filepath)))

    return render_template("upload.html")


@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)