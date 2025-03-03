from flask import Flask, render_template
import requests

# Initialize Flask application
app = Flask(__name__)

# Add Meme Generator
def get_meme():
    url = "https://meme-api.com/gimme"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()  # Properly parse JSON

        # Ensure 'preview' exists and has enough elements
        if "preview" in data and len(data["preview"]) > 1:
            meme_large = data["preview"][-2]  # Get the second last preview image
        else:
            meme_large = data.get("url", "https://i.imgur.com/ZfQ2z0A.jpeg")  # Fallback

        subreddit = data.get("subreddit", "Unknown")
        return meme_large, subreddit
    except requests.exceptions.RequestException as e:
        print(f"Error fetching meme: {e}")
        return "https://i.imgur.com/ZfQ2z0A.jpeg", "Error"

# Define a route for the home page
@app.route('/')
def home():
    meme_pic,subreddit = get_meme()
    return render_template('index.html', meme_pic=meme_pic, subreddit=subreddit)

# Run the application
if __name__ == '__main__':
    app.run()