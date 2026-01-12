# KiteInfi Frontend - Backend API Integration

## Overview
This document describes the integration between the frontend and the KiteInfi backend API.

## Integrated Endpoints

### 1. Market Chatbot (Sync) - `/market_chatbot/sync`
**Method:** POST  
**Description:** Synchronous endpoint for market-related queries  
**Request Body:**
```json
{
  "user_query": "What's the market sentiment today?"
}
```
**Response:**
```json
{
  "response": "The market sentiment is..."
}
```
**Used in:** `src/pages/Chat.jsx`

### 2. Portfolio Chatbot (Sync) - `/portfolio_chatbot/sync`
**Method:** POST  
**Description:** Synchronous endpoint for portfolio-related queries  
**Request Body:**
```json
{
  "user_query": "Show my P/L by sector"
}
```
**Response:**
```json
{
  "response": "Your portfolio P/L by sector..."
}
```
**Used in:** `src/pages/PortfolioChat.jsx`

### 3. Portfolio Report - `/portfolio/report`
**Method:** POST  
**Description:** Generates and emails a comprehensive portfolio report  
**Request Body:** None  
**Response:**
```json
{
  "status": "success",
  "message": "Portfolio report generated and emailed successfully"
}
```
**Used in:** `src/pages/Reports.jsx`

### 4. Health Check - `/health`
**Method:** GET  
**Description:** Checks the health status of all backend services  
**Response:**
```json
{
  "status": "healthy",
  "services": {
    "market_chatbot": "ready",
    "portfolio_chatbot": "ready",
    "portfolio_report": "ready"
  }
}
```
**Used in:** `src/pages/Reports.jsx`

## API Service File

All API calls are centralized in `src/services/api.js` which provides:

- **`marketChatbotSync(userQuery)`** - Call market chatbot
- **`portfolioChatbotSync(userQuery)`** - Call portfolio chatbot
- **`generatePortfolioReport()`** - Generate portfolio report
- **`healthCheck()`** - Check backend health

## Configuration

The backend URL is configured via environment variable in `.env`:

```
REACT_APP_API_URL=http://localhost:8000
```

## Error Handling

All API functions include comprehensive error handling:
- Network errors
- HTTP error responses
- Invalid JSON responses
- Empty/whitespace responses

Errors are logged to console and user-friendly messages are displayed in the UI.

## Usage Examples

### Market Chat
```javascript
import { marketChatbotSync } from '../services/api';

const response = await marketChatbotSync("What's the Nifty 50 trend?");
console.log(response.response);
```

### Portfolio Chat
```javascript
import { portfolioChatbotSync } from '../services/api';

const response = await portfolioChatbotSync("Show my top holdings");
console.log(response.response);
```

### Generate Report
```javascript
import { generatePortfolioReport } from '../services/api';

const result = await generatePortfolioReport();
console.log(result.message);
```

### Health Check
```javascript
import { healthCheck } from '../services/api';

const health = await healthCheck();
console.log(health.status); // "healthy"
console.log(health.services); // { market_chatbot: "ready", ... }
```

## Testing

To test the integration:

1. Start the backend server:
   ```bash
   cd backend/KiteInfi
   python main.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm start
   ```

3. Navigate to:
   - Market Chat: http://localhost:3000/chat
   - Portfolio Chat: http://localhost:3000/portfolio
   - Reports: http://localhost:3000/reports

## Notes

- The backend must be running on port 8000 (or update REACT_APP_API_URL)
- CORS is configured in the backend to allow requests from http://localhost:3000
- All endpoints use JSON for request/response bodies
- The sync endpoints were chosen over streaming for simpler integration
