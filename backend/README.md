# TukuyBooks Node.js Backend

This is the Node.js backend API for TukuyBooks, deployed on Vercel. It provides an interface for the frontend while still leveraging Python spiders for content scraping.

## Requirements

- Node.js 16+
- npm or yarn
- Python 3.8+ (for running the spiders)
- Required Python packages (see `backend/requirements.txt`)

## Getting Started

### Installing Dependencies

#### Node.js Dependencies

```bash
cd backend
npm install
```

#### Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Running the Backend Locally

```bash
cd backend
npm run dev
```

This will start the backend on <http://localhost:3000>.

## API Endpoints

- `/api/spiders` - Get list of available spiders
- `/api/spiders/:id/run` - Run a specific spider
- `/api/spiders/:id/status` - Get status of a spider run
- `/api/spiders/:id/ebook` - Generate an ebook from scraped data
- `/api/ebooks` - Get list of available ebooks
- `/api/download/:filename` - Download a specific file
- `/_vercel/health` - Health check endpoint for Vercel monitoring

## Architecture

This backend uses:

- **Express.js**: For the HTTP server and API endpoints
- **PythonShell**: For running Python spiders from Node.js
- **Vercel Serverless**: For deployment

## Deployment to Vercel

To deploy to Vercel:

```bash
cd backend
vercel --prod
```

## Code Structure

- `api/index.js`: Main Express application
- `api/spiderRunner.js`: Utilities for running Python spiders from Node.js
- `scripts/spider_runner.py`: Python script for executing spiders
- `scripts/make_ebook.py`: Python script for generating ebooks
- `spiders/`: Directory containing the spiders
