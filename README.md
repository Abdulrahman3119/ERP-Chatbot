# IDO Assistant

AI-powered assistant for interacting with the IDO system. This assistant helps users query data, generate reports, and interact with IDO DocTypes through natural language.

## Features

- 🤖 Natural language interaction with IDO system
- 📊 High-accuracy report generation
- 💬 Conversation memory and context awareness
- 🔍 Intelligent DocType search and filtering
- 🛠️ RESTful API and CLI interfaces

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the **project root** (same directory as `requirements.txt`):

```bash
# Copy the example template (if available) or create manually
cp .env.example .env
```

Or create `.env` manually with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# IDO System API Configuration
# Note: Environment variable names use ERPNEXT_ prefix for backward compatibility
# but the system now refers to IDO
ERPNEXT_BASE_URL=https://your-ido-instance.com
ERPNEXT_API_KEY=your_ido_api_key_here
ERPNEXT_API_SECRET=your_ido_api_secret_here
```

**Important:** The `.env` file should be placed in the project root directory:
```
erp-assistant/
├── .env              ← Place your .env file here
├── app/
├── requirements.txt
└── README.md
```

### 3. Run the Application

#### API Server (FastAPI)

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Chat Endpoint: `POST http://localhost:8000/chat`

#### CLI Interface

```bash
python -m app.presentation.cli
```

## API Usage

### Chat Endpoint

```bash
POST /chat
Content-Type: application/json

{
  "message": "Show me all customers",
  "conversation_id": "optional-conversation-id",
  "include_history": true
}
```

Response:
```json
{
  "reply": "Here are all the customers...",
  "conversation_id": "conv_1234567890"
}
```

### Conversation Memory

The API supports conversation memory by using the `conversation_id` parameter:
- Include the same `conversation_id` in subsequent requests to maintain context
- Conversations are stored in memory for 24 hours
- Last 20 messages are kept for context

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `ERPNEXT_BASE_URL` | Base URL of your IDO instance | Yes |
| `ERPNEXT_API_KEY` | IDO API key | Yes |
| `ERPNEXT_API_SECRET` | IDO API secret | Yes |

## Project Structure

```
erp-assistant/
├── app/
│   ├── api/              # FastAPI application
│   ├── application/      # Business logic (services)
│   ├── config/           # Configuration and settings
│   ├── infrastructure/   # External clients (IDO API)
│   └── presentation/     # Agent, tools, and CLI
├── .env                  # Environment variables (create this)
├── .gitignore
├── requirements.txt
└── README.md
```

## Features in Detail

### Report Generation
The assistant can generate comprehensive reports when users request:
- Sales reports
- Inventory reports
- Financial reports
- Custom data analysis

### Conversation Context
- Maintains context across multiple messages
- Understands references like "it", "that", "the previous one"
- Remembers previous queries and responses

### DocType Intelligence
- Handles typos and misspellings
- Suggests correct DocType names
- Intelligent field filtering

## Development

### Running Tests

```bash
# Add your test commands here
```

### Code Style

The project follows Python best practices and uses type hints throughout.

## License

[Add your license here]
