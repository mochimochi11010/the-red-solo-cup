# The Red Solo Cup: Cocktail Recommendation Web App

# Set-Up
Clone repo from Github and download it onto Desktop
Navigate to the repo using the command line (this an example of what to run that works for Karen's Macbook):
```sh
cd /Users/karen/Documents/GitHub/the-red-solo-cup
```

Create a virtual environment:

```sh
conda create -n red-solo-cup-env python=3.13
```

Activate the virtual environment:

```sh
conda activate red-solo-cup-env
```

Install package dependencies:

```sh
pip install -r requirements.txt
```

# Google / YouTube API Setup(optional)

The Red Solo Cup can display embedded YouTube cocktail tutorial videos using the YouTube Data API v3.
This feature requires a free API key from Google. Create or edit a `.env` file in the root directory of the project and add, the API key can be found in the secret credential section of the repo :

```sh
YOUTUBE_API_KEY=your-youtube-api-key-here
```

# Usage

Cocktail Recipe Finder Web App - enter alcohols and mixers you have to get personalized cocktail recommendations with images and recipes

```sh
python run.py
```

# Testing

Run tests:

```sh
pytest
```

# Configuration

The web app requires a Flask secret key for session management. Create a local ".env" file and store your environment variable in there:

```sh
# this is the ".env" file...

FLASK_APP=web_app
SECRET_KEY=super-secret-flask-key-fall-2025-for-cocktail-app
```

### Optional: YouTube API Integration

To enable embedded YouTube video tutorials on cocktail detail pages, add a YouTube Data API key to your ".env" file:

```sh
YOUTUBE_API_KEY=your-youtube-api-key-here
```

**How to get a YouTube API key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Add the API key to your .env file

**Without API key:** The app will display a "Search YouTube Tutorials" button that links to YouTube search results for the cocktail.

**With API key:** The app will embed the first relevant YouTube tutorial video directly on the cocktail detail page.

### Web App

Run the web app (then view in the browser at http://127.0.0.1:5000/):

```sh
FLASK_APP=web_app flask run
```
