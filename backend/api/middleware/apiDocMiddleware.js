/**
 * API Documentation middleware
 */

const apiDoc = require("../config/api-doc");

/**
 * Serve API documentation
 */
function serveApiDoc(req, res) {
  res.json(apiDoc);
}

module.exports = {
  serveApiDoc,
};
