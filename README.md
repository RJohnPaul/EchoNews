 # NewsAI
 
<p align="center">
  <img src="https://github.com/RJohnPaul/newsAI/blob/049305feb7bb35d97b7641d009a83268ce657395/Template%20Example.png" alt="YouNotes Logo"/>
</p>


NewsAI is an AI-powered personalized news aggregation and summarization web application. It fetches articles from multiple RSS feeds, processes them using AI models, and provides concise summaries to users. Inspired by the [Next.js FastAPI boilerplate](https://github.com/digitros/nextjs-fastapi), this project integrates Next.js for the frontend and FastAPI for the backend.

## Features
- **Personalized News Feed**: Fetches articles from multiple RSS sources.
- **AI Summarization**: Uses LLaMA or other AI models to generate concise summaries.
- **Category-Based Filtering**: Users can filter news based on categories.
- **Responsive UI**: Optimized for both desktop and mobile devices.
- **Efficient API Handling**: Utilizes FastAPI for backend processing.

## Tech Stack
- **Frontend**: Next.js, React, TailwindCSS
- **Backend**: FastAPI, Python
- **Database**: PostgreSQL (Supabase)
- **AI Models**: LLaMA for summarization
- **Hosting**: Vercel (Frontend), Render (Backend)


### Prerequisites
Ensure you have the following installed:
- Node.js (>= 16.x)
- Python (>= 3.8)

### Clone the Repository
```bash
git clone https://github.com/RJohnPaul/newsAI.git
cd newsAI
```

### Install Frontend Dependencies
```bash
npm install
```

### Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
npm run api-all
```
This will start both the Next.js frontend and FastAPI backend.

## API Endpoints
The FastAPI backend exposes several endpoints:

- **Fetch Articles**: `/api/fetch-articles` (Fetches RSS feed articles)
- **Summarize Article**: `/api/summarize` (Generates AI-based summary)
- **Get Categories**: `/api/categories` (Lists available categories)

## Contribution
1. Fork the repository
2. Create a new feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m "Added new feature"`)
4. Push to your fork and submit a pull request


---
This project was built using the [Next.js FastAPI boilerplate](https://github.com/digitros/nextjs-fastapi) as a base.

