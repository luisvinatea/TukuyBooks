# TukuyBooks API

This is the backend API for TukuyBooks, deployed on Vercel.

## API Endpoints

- `/api/spiders`: Get list of available spiders
- `/api/spiders/:id/run`: Run a specific spider
- `/api/spiders/:id/status`: Get status of a spider run
- `/api/spiders/:id/ebook`: Generate an ebook from scraped data
- `/api/ebooks`: Get list of available ebooks
- `/api/download/:filename`: Download a specific file

## Deployment

This API is configured for deployment to Vercel. The main entry point is `api/index.py`.

### Configuration

- `vercel.json`: Main deployment configuration
- `api/requirements.txt`: Python dependencies
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
