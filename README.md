# EchoNews: AI-Powered News Aggregation Platform

<p align="center">
  <img src="https://github.com/RJohnPaul/newsAI/blob/5de1faa521a7c5651845d2cac8d6781c6e1bb9e7/Template%20Example%20(1).png" alt="EchoNews Logo"/>
</p>

## Overview

EchoNews is a sophisticated AI-powered news aggregation and summarization platform that transforms how users consume digital content. Leveraging cutting-edge artificial intelligence, EchoNews automatically collects articles from diverse RSS feeds, processes them through advanced machine learning models, and delivers personalized, concise summaries tailored to individual preferences. Built on a robust architecture integrating Next.js for the frontend and FastAPI for the backend, EchoNews creates an intuitive and seamless news experience.

## Key Features

- **Intelligent News Personalization**: Advanced algorithm that curates content from multiple RSS sources based on user preferences and reading patterns
- **State-of-the-Art AI Summarization**: Utilizes LLaMA and other sophisticated AI models to generate comprehensive yet concise article summaries while preserving key information
- **Dynamic Category Navigation**: Intuitive filtering system allowing users to explore news across multiple dimensions and interests
- **Responsive Cross-Platform Design**: Meticulously crafted interface optimized for seamless experiences across desktop, tablet, and mobile devices
- **High-Performance Backend**: Scalable FastAPI architecture ensuring rapid response times and efficient data processing

## Technical Architecture

### Frontend
- **Framework**: Next.js with React for component-based UI development
- **Styling**: TailwindCSS for responsive design and consistent visual identity
- **State Management**: React Context API and custom hooks for efficient state handling

### Backend
- **API Framework**: FastAPI for high-performance, asynchronous request handling
- **Language**: Python 3.8+ with type annotations
- **Data Processing**: Custom NLP pipelines for content analysis

### Infrastructure
- **To Do ->** `Database: PostgreSQL hosted on Supabase for reliable data persistence`
- **AI Integration**: LLaMA model optimized for text summarization tasks
- **Deployment**: Vercel for frontend services, Render for backend processes and fastapi initialization

## Installation Guide

### Prerequisites
Before beginning installation, ensure your development environment includes:
- Node.js (version 16.x or higher)
- Python (version 3.8 or higher)
- Git for version control

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/RJohnPaul/newsAI.git
   cd newsAI
   ```

2. **Configure Frontend Environment**
   ```bash
   npm install
   ```

3. **Prepare Backend Services**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Development Environment**
   ```bash
   npm run api-all
   ```
   This command initializes both the Next.js frontend server and FastAPI backend services simultaneously.

## Localhost Running

- replace the const ```bash BASE_URL = "http://127.0.0.1:8000" ```  at **api/news/route.ts** and change env value of ```NEXT_PUBLIC_API_URL```


## API Documentation

The EchoNews backend exposes several RESTful endpoints for integration:

- **Article Retrieval**: `/api/news/sources/{language}`
  - Gets list of available news sources for a specific language

- **Main Article Fetching**: `/api/news`
  - Returns article without language
  - Includes article counts and relationship metadata

- **Api Running Checker**: `/api/Helloapi`
  - Returns a sample message : "Hello from FastAPI powered by Gemini 1.5 Flash"
  - This makes sure the api is running in backend

## Research Papers based on concept
 - [IEEE-Explore-paper-1](https://ieeexplore.ieee.org/document/5072521)
 - [IEEE-Explore-paper-2](https://ieeexplore.ieee.org/document/5578100)
## Contributing to EchoNews

We welcome contributions from developers of all skill levels. To contribute:

1. Fork the official repository
2. Create a feature branch with descriptive naming (`git checkout -b feature/enhanced-summarization`)
3. Implement your changes with appropriate tests
4. Commit with clear, descriptive messages (`git commit -m "Implemented enhanced summarization algorithm"`)
5. Push to your fork and submit a detailed pull request

## Updates
 - Modified and Boosted the API fetching speed from 13.82 s to 4 - 6 s (approx)

## Why Not Try on Collab?

- There is a [ML-Model](https://colab.research.google.com/drive/1PkJF65fwN8w_OoccX2jg0o1P8Cjzp6ah?usp=sharing) which is in google collab and can be used to test the model

---

This project is built upon the architectural foundation of the [Next.js FastAPI boilerplate](https://github.com/digitros/nextjs-fastapi), extending it with custom AI capabilities and news-specific features.
