# YouTube API Setup Guide

This guide will help you set up YouTube video tutorials for cocktail recipes in the Red Solo Cup application.

## Why is this needed?

To display actual YouTube video tutorials directly on the cocktail detail pages, the application needs to search YouTube's video database using the YouTube Data API. This requires a free API key from Google.

## Step-by-Step Setup Instructions

### 1. Go to Google Cloud Console
Visit: https://console.cloud.google.com/

### 2. Create a New Project
- Click on the project dropdown at the top
- Click "New Project"
- Name it something like "Red Solo Cup" or "Cocktail App"
- Click "Create"

### 3. Enable YouTube Data API v3
- Once your project is created, make sure it's selected
- Go to "APIs & Services" → "Library"
- Search for "YouTube Data API v3"
- Click on it and press "ENABLE"

### 4. Create API Credentials
- Go to "APIs & Services" → "Credentials"
- Click "Create Credentials" → "API Key"
- A popup will show your new API key - copy it!
- (Optional but recommended) Click "Restrict Key" and:
  - Under "API restrictions", select "Restrict key"
  - Check only "YouTube Data API v3"
  - Click "Save"

### 5. Add API Key to Your Application
Create or edit the `.env` file in your project root directory:

```bash
# Add this line to your .env file
YOUTUBE_API_KEY=your-api-key-here
```

Replace `your-api-key-here` with the actual API key you copied.

### 6. Restart the Flask Server
Stop the current server (Ctrl+C) and start it again:

```bash
python run.py
```

## What You'll See

### With API Key Configured:
- ✅ Full embedded YouTube videos on every cocktail detail page
- ✅ Videos play directly on your website
- ✅ Automatic search for the best tutorial video for each cocktail

### Without API Key:
- ⚠️ A helpful warning message with setup instructions
- 🔗 Link to search YouTube manually

## Free Quota Information

The YouTube Data API has a free quota:
- **10,000 units per day** (free tier)
- Each video search costs **100 units**
- This allows **100 video searches per day** for free
- More than enough for personal/development use!

## Troubleshooting

### "API key not found" warning
- Make sure the `.env` file is in the root directory of your project
- Check that the line is: `YOUTUBE_API_KEY=your-key-here` (no spaces around `=`)
- Restart the Flask server after adding the key

### "Quota exceeded" error
- You've used your daily quota of 10,000 units
- Wait until the next day (quota resets at midnight Pacific Time)
- Or request a quota increase from Google Cloud Console

### Videos not loading
- Check that YouTube Data API v3 is enabled in your Google Cloud project
- Verify your API key is correctly copied
- Check the terminal for any error messages

## Security Note

**Important:** Never commit your `.env` file to Git/GitHub!

The `.gitignore` file should already include `.env`, but double-check:

```bash
# Make sure .env is in .gitignore
cat .gitignore | grep .env
```

## Alternative: Without API Key

If you don't want to set up an API key, the app will still work! It will show a link to search YouTube instead of embedding videos directly.

---

**Need Help?** Check the official documentation:
- [YouTube Data API Overview](https://developers.google.com/youtube/v3/getting-started)
- [Google Cloud Console](https://console.cloud.google.com/)
