# Hopscotch Support Bot - Vercel Deployment

This project is a Vercel-ready version of the original Gradio chatbot.

## Project structure

- `index.html` - chatbot frontend
- `api/chat.py` - Python serverless API
- `requirements.txt` - Python dependencies
- `vercel.json` - Vercel configuration
- `.env.example` - environment variable template
- `.gitignore` - prevents secrets from being committed

## 1. Local setup

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_actual_openrouter_api_key
```

Do NOT commit `.env` to GitHub.

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Push to GitHub

```bash
git init
git add .
git commit -m "Initial chatbot deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

## 3. Deploy to Vercel

Import the GitHub repository into Vercel.

In Vercel:

Project Settings -> Environment Variables

Add:

```text
Name: OPENROUTER_API_KEY
Value: your actual OpenRouter API key
```

Then redeploy.

## Important

Never put your real OpenRouter API key in:

- `index.html`
- GitHub
- `vercel.json`
- any JavaScript code

The API key should only exist in your local `.env` and Vercel Environment Variables.

## Note

The original Hugging Face `spaces` package and `@spaces.GPU` decorator were removed because they are not required for Vercel.
