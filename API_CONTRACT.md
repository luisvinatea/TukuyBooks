# TukuyBooks API Contract

This document defines the contract between the TukuyBooks frontend and backend. It specifies the expected request and response formats for all API endpoints.

## API Base URL

- **Production**: `https://tukuybooks.vercel.app/api`
- **Development**: `http://localhost:3000/api`

## Authentication

Currently, the API does not require authentication.

## Response Format

All API responses follow this standardized format:

```json
{
  "success": true|false,
  "message": "Human readable message",
  "timestamp": "ISO-8601 timestamp",
  "data": { /* Response data object (when success is true) */ },
  "error": "Error details (when success is false)"
}
```

## API Endpoints

### Spider Management

#### Get Available Spiders

- **URL**: `/spiders`
- **Method**: `GET`
- **Success Response**:

  ```json
  {
    "success": true,
    "message": "Spiders retrieved successfully",
    "timestamp": "2025-05-13T10:30:00.000Z",
    "data": {
      "spiders": [
        {
          "id": "python_docs",
          "name": "Python Documentation",
          "description": "Scrapes Python 3 documentation",
          "module": "backend.spiders.python_docs_spider",
          "class": "PythonDocsSpider",
          "output_prefix": "Python3Docs"
        }
      ]
    }
  }
  ```

#### Get Spider Details

- **URL**: `/spiders/{id}`
- **Method**: `GET`
- **URL Parameters**: `id=[string]` - ID of the spider
- **Success Response**:

  ```json
  {
    "success": true,
    "message": "Spider retrieved successfully",
    "timestamp": "2025-05-13T10:30:00.000Z",
    "data": {
      "spider": {
        "id": "python_docs",
        "name": "Python Documentation",
        "description": "Scrapes Python 3 documentation",
        "module": "backend.spiders.python_docs_spider",
        "class": "PythonDocsSpider",
        "output_prefix": "Python3Docs"
      }
    }
  }
  ```

- **Error Responses**:
  - `404 Not Found`: Spider with the given ID does not exist

#### Run Spider

- **URL**: `/spiders/{id}/run`
- **Method**: `POST`
- **URL Parameters**: `id=[string]` - ID of the spider
- **Success Response**:

  ```json
  {
    "success": true,
    "message": "Spider python_docs started successfully",
    "timestamp": "2025-05-13T10:30:00.000Z",
    "runId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running"
  }
  ```

- **Error Responses**:
  - `404 Not Found`: Spider with the given ID does not exist
  - `500 Server Error`: Error starting the spider

#### Get Spider Run Status

- **URL**: `/spiders/{id}/status`
- **Method**: `GET`
- **URL Parameters**: `id=[string]` - ID of the spider
- **Query Parameters**: `runId=[string]` - ID of the run
- **Success Response**:

  ```json
  {
    "success": true,
    "message": "Spider status retrieved",
    "timestamp": "2025-05-13T10:30:00.000Z",
    "data": {
      "status": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "spiderId": "python_docs",
        "status": "running",
        "startTime": "2025-05-13T10:25:00.000Z",
        "progress": 45
      }
    }
  }
  ```

- **Error Responses**:
  - `400 Bad Request`: Missing required runId parameter
  - `404 Not Found`: Run ID not found

### Ebook Management

#### Generate Ebook

- **URL**: `/spiders/{id}/ebook`
- **Method**: `POST`
- **URL Parameters**: `id=[string]` - ID of the spider
- **Request Body**:

  ```json
  {
    "format": "epub", // Optional: "epub", "pdf", or "mobi" (default: "epub")
    "title": "Python 3 Documentation" // Optional: title for the ebook
  }
  ```

- **Success Response**:

  ```json
  {
    "success": true,
    "message": "E-book generated successfully",
    "timestamp": "2025-05-13T10:30:00.000Z",
    "data": {
      "filename": "python_docs_1621234567890.epub",
      "format": "epub",
      "path": "/path/to/ebook/file.epub",
      "title": "Python 3 Documentation"
    }
  }
  ```

- **Error Responses**:
  - `400 Bad Request`: No data found for the spider (needs to be run first)
  - `404 Not Found`: Spider with the given ID does not exist
  - `500 Server Error`: Error generating the ebook

#### List Available Ebooks

- **URL**: `/ebooks`
- **Method**: `GET`
- **Success Response**:

  ```json
  {
    "success": true,
    "message": "Ebooks retrieved successfully",
    "timestamp": "2025-05-13T10:30:00.000Z",
    "data": {
      "ebooks": [
        {
          "filename": "python_docs_1621234567890.epub",
          "spiderId": "python_docs",
          "format": "epub",
          "size": 1234567,
          "created": "2025-05-13T10:15:00.000Z"
        }
      ]
    }
  }
  ```

### File Download

#### Download File

- **URL**: `/download/{filename}`
- **Method**: `GET`
- **URL Parameters**: `filename=[string]` - Name of the file to download
- **Success Response**: The file as a download
- **Error Responses**:
  - `404 Not Found`: File not found

## Error Handling

The frontend should handle error cases by checking the `success` field in the response. When `success` is `false`, there will be an `error` field with details about what went wrong.

## Frontend-Backend Integration Guidelines

1. **Status Polling**: When running spiders, the frontend should poll the status endpoint at regular intervals (e.g., every 2-5 seconds) to update the UI with progress information.

2. **Error Handling**: The frontend should provide appropriate feedback to users based on error messages from the API.

3. **File Download**: For ebook downloads, the frontend should direct the user's browser to the download URL.

4. **Loading States**: The frontend should show loading indicators during API operations that might take time to complete.

5. **Retry Logic**: The frontend should implement retry logic for transient network errors, but should limit the number of retries to avoid overwhelming the server.
