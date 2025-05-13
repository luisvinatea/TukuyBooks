# TukuyBooks API

This is the backend API for TukuyBooks, deployed on Vercel.

## API Endpoints

- `/api/spiders`: Get list of available spiders
- `/api/spiders/:id/run`: Run a specific spider
- `/api/spiders/:id/status`: Get status of a spider run
- `/api/spiders/:id/ebook`: Generate an ebook from scraped data
- `/api/ebooks`: Get list of available ebooks
- `/api/download/:filename`: Download a specific file
- `/_vercel/health`: Health check endpoint for Vercel monitoring

## Deployment

This API is configured for deployment to Vercel. The main entry point is `api/index.py`.

### Vercel Configuration

The API is deployed using a single `vercel.json` configuration file in the `backend` directory, with these key features:

- **Functions**: Used instead of the legacy `builds` property for improved memory and runtime control
- **Rewrites**: Used instead of the legacy `routes` property to avoid conflicts with headers
- **Headers**: Properly configured CORS headers for API requests

### Avoiding Configuration Conflicts

We've implemented these best practices to avoid Vercel configuration conflicts:

1. Using only one configuration file (`vercel.json`) instead of multiple
2. Using modern Vercel configuration properties (`functions`, `rewrites`) instead of legacy ones (`builds`, `routes`)
3. Proper separation of concerns between routing and CORS headers

### Dependencies

- `api/requirements.txt`: Python dependencies including Flask, Scrapy, and other required packages
- `api/runtime.txt`: Specifies the Python version

### Development vs Production

When developing locally, the API runs as a standard Flask application. On Vercel, it runs as a serverless function with appropriate handlers for request processing.

- `api/runtime.txt`: Python version specification

### Environment Variables

The following environment variables are used:

- `PYTHONPATH`: Set to `.` for proper module imports
- `VERCEL_DEPLOYMENT`: Set to `true` to enable Vercel-specific code paths
- `FLASK_ENV`: Set to `production` for production deployments

## Local Development

To develop locally, run:

```bash
cd backend
pip install -r api/requirements.txt
python -m flask --app api/app run --debug
```

## Deployment URL

The API is deployed at: <https://tukuybooks.vercel.app>
