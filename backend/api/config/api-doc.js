/**
 * API Documentation Module
 * This provides JSON schema documentation for all API endpoints
 */

const apiDoc = {
  openapi: "3.0.0",
  info: {
    title: "TukuyBooks API",
    version: "1.0.0",
    description: "API for managing documentation spiders and ebook generation",
  },
  servers: [
    {
      url: "https://tukuybooks.vercel.app/api",
      description: "Production server",
    },
    {
      url: "http://localhost:3000/api",
      description: "Local development server",
    },
  ],
  tags: [
    {
      name: "Spiders",
      description: "Web scraping spiders for documentation sites",
    },
    {
      name: "Ebooks",
      description: "Ebook generation and management",
    },
    {
      name: "Download",
      description: "File download operations",
    },
  ],
  paths: {
    "/spiders": {
      get: {
        tags: ["Spiders"],
        summary: "Get list of available spiders",
        responses: {
          200: {
            description: "A list of available spiders",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean" },
                    message: { type: "string" },
                    data: {
                      type: "object",
                      properties: {
                        spiders: {
                          type: "array",
                          items: {
                            type: "object",
                            properties: {
                              id: { type: "string" },
                              name: { type: "string" },
                              description: { type: "string" },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/spiders/{id}": {
      get: {
        tags: ["Spiders"],
        summary: "Get details about a specific spider",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            description: "Spider ID",
            schema: { type: "string" },
          },
        ],
        responses: {
          200: {
            description: "Spider details",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean" },
                    message: { type: "string" },
                    data: {
                      type: "object",
                      properties: {
                        spider: {
                          type: "object",
                          properties: {
                            id: { type: "string" },
                            name: { type: "string" },
                            description: { type: "string" },
                            module: { type: "string" },
                            class: { type: "string" },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          404: {
            description: "Spider not found",
          },
        },
      },
    },
    "/spiders/{id}/run": {
      post: {
        tags: ["Spiders"],
        summary: "Run a specific spider",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            description: "Spider ID",
            schema: { type: "string" },
          },
        ],
        responses: {
          200: {
            description: "Spider started successfully",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean" },
                    message: { type: "string" },
                    runId: { type: "string" },
                    status: { type: "string" },
                  },
                },
              },
            },
          },
          404: {
            description: "Spider not found",
          },
          500: {
            description: "Server error",
          },
        },
      },
    },
    "/spiders/{id}/status": {
      get: {
        tags: ["Spiders"],
        summary: "Get status of a spider run",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            description: "Spider ID",
            schema: { type: "string" },
          },
          {
            name: "runId",
            in: "query",
            required: true,
            description: "Run ID from the spider run operation",
            schema: { type: "string" },
          },
        ],
        responses: {
          200: {
            description: "Spider run status",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean" },
                    message: { type: "string" },
                    data: {
                      type: "object",
                      properties: {
                        status: {
                          type: "object",
                          properties: {
                            id: { type: "string" },
                            spiderId: { type: "string" },
                            status: {
                              type: "string",
                              enum: [
                                "starting",
                                "running",
                                "completed",
                                "failed",
                              ],
                            },
                            startTime: { type: "string", format: "date-time" },
                            endTime: { type: "string", format: "date-time" },
                            progress: { type: "number" },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          404: {
            description: "Run ID not found",
          },
        },
      },
    },
    "/spiders/{id}/ebook": {
      post: {
        tags: ["Ebooks"],
        summary: "Generate an ebook from spider data",
        parameters: [
          {
            name: "id",
            in: "path",
            required: true,
            description: "Spider ID",
            schema: { type: "string" },
          },
        ],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  format: {
                    type: "string",
                    enum: ["epub", "pdf", "mobi"],
                    default: "epub",
                  },
                  title: {
                    type: "string",
                    description: "Title for the ebook",
                  },
                },
              },
            },
          },
        },
        responses: {
          200: {
            description: "Ebook generated successfully",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean" },
                    message: { type: "string" },
                    data: {
                      type: "object",
                      properties: {
                        filename: { type: "string" },
                        format: { type: "string" },
                        path: { type: "string" },
                        title: { type: "string" },
                      },
                    },
                  },
                },
              },
            },
          },
          400: {
            description: "Missing data files",
          },
          404: {
            description: "Spider not found",
          },
          500: {
            description: "Server error",
          },
        },
      },
    },
    "/ebooks": {
      get: {
        tags: ["Ebooks"],
        summary: "List available ebooks",
        responses: {
          200: {
            description: "List of ebooks",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    success: { type: "boolean" },
                    message: { type: "string" },
                    data: {
                      type: "object",
                      properties: {
                        ebooks: {
                          type: "array",
                          items: {
                            type: "object",
                            properties: {
                              filename: { type: "string" },
                              spiderId: { type: "string" },
                              format: { type: "string" },
                              size: { type: "number" },
                              created: { type: "string", format: "date-time" },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          500: {
            description: "Server error",
          },
        },
      },
    },
    "/download/{filename}": {
      get: {
        tags: ["Download"],
        summary: "Download a file",
        parameters: [
          {
            name: "filename",
            in: "path",
            required: true,
            description: "Filename to download",
            schema: { type: "string" },
          },
        ],
        responses: {
          200: {
            description: "File download",
            content: {
              "application/octet-stream": {
                schema: {
                  type: "string",
                  format: "binary",
                },
              },
            },
          },
          404: {
            description: "File not found",
          },
          500: {
            description: "Server error",
          },
        },
      },
    },
  },
};

module.exports = apiDoc;
