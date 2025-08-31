# Multi-Model Chat Interface

A modern chat interface that supports multiple AI providers including OpenAI, Google Gemini, and Anthropic Claude. Built with Python FastAPI backend and React TypeScript frontend.

## Features

- **Multi-Provider Support**: Switch between OpenAI, Google Gemini, and Anthropic models
- **Real-time Chat**: Instant messaging with AI models
- **Conversation Management**: Create, edit, delete, and organize conversations
- **Model Configuration**: Adjust temperature, max tokens, and system prompts
- **Modern UI**: Beautiful, responsive interface built with React and Tailwind CSS
- **Structured Architecture**: Clean separation between backend and frontend

## Tech Stack

### Backend
- **Python 3.8+**
- **FastAPI**: Modern web framework for building APIs
- **Pydantic**: Data validation and settings management
- **uvicorn**: ASGI server for running the application

### Frontend
- **React 18**: Modern React with TypeScript
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **Axios**: HTTP client for API calls

## Project Structure

```
memoryRAG/
├── backend/                    # Python backend
│   ├── app/
│   │   ├── api/               # API route handlers
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Business logic and AI adapters
│   │   ├── config.py          # Configuration management
│   │   └── main.py           # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── env_example.txt       # Environment variables template
├── src/                       # React frontend
│   ├── components/           # React components
│   ├── services/            # API client
│   ├── store/              # State management
│   ├── types/              # TypeScript types
│   └── App.tsx            # Main application component
├── package.json           # Node.js dependencies
└── README.md             # This file
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- API keys for at least one of the supported providers:
  - OpenAI API key
  - Google AI API key
  - Anthropic API key

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

5. **Run the backend server:**
   ```bash
   python -m app.main
   ```
   
   Or with uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to the project root:**
   ```bash
   cd ..  # If you're in the backend directory
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

### Chat Endpoints
- `POST /api/chat/send` - Send a message and get AI response
- `GET /api/chat/conversations` - Get all conversations
- `GET /api/chat/conversations/{id}` - Get specific conversation
- `POST /api/chat/conversations` - Create new conversation
- `DELETE /api/chat/conversations/{id}` - Delete conversation
- `PUT /api/chat/conversations/{id}/title` - Update conversation title
- `DELETE /api/chat/conversations/{id}/messages` - Clear conversation

### Model Endpoints
- `GET /api/chat/models` - Get available AI models

## Usage

1. **Start the Backend**: Follow the backend setup instructions to start the FastAPI server
2. **Start the Frontend**: Run the React development server
3. **Configure API Keys**: Make sure you have valid API keys in your `.env` file
4. **Create a Conversation**: Click "New Conversation" in the sidebar
5. **Select a Model**: Go to Settings tab to choose your preferred AI provider and model
6. **Start Chatting**: Type your message and press Enter to chat with the AI

## Model Providers

### OpenAI
- GPT-4 Turbo
- GPT-4
- GPT-3.5 Turbo

### Google Gemini
- Gemini Pro
- Gemini Pro Vision

### Anthropic Claude
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

## Configuration Options

- **Temperature**: Controls randomness (0.0 = focused, 2.0 = creative)
- **Max Tokens**: Maximum length of AI responses
- **System Prompt**: Custom instructions for the AI's behavior

## Development

### Running Tests
```bash
# Backend tests (if implemented)
cd backend
python -m pytest

# Frontend tests (if implemented)
npm test
```

### Building for Production
```bash
# Frontend build
npm run build

# Backend deployment with gunicorn (recommended for production)
cd backend
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

1. **API Key Errors**: Make sure your API keys are correctly set in the `.env` file
2. **CORS Issues**: Ensure the frontend URL is included in `ALLOWED_ORIGINS`
3. **Model Not Available**: Check that the selected model is supported by your API key
4. **Connection Refused**: Verify that the backend server is running on port 8000

### Getting Help

- Check the API documentation at http://localhost:8000/docs
- Review the browser console for frontend errors
- Check the backend logs for API errors
