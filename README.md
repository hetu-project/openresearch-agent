# OpenResearch Agent

An intelligent AI-powered research agent for academic literature analysis and exploration.

## Overview

OpenResearch Agent is a sophisticated academic research assistant that leverages Large Language Models (LLMs) and Model Control Protocol (MCP) to provide intelligent analysis of academic papers, authors, research trends, and citation networks. The system combines natural language processing with structured academic data to deliver comprehensive research insights.

## Features

### 🔍 **Intelligent Query Processing**
- Natural language understanding for academic queries
- Intent analysis and classification
- Context-aware response generation
- Multi-turn conversation support

### 📚 **Academic Research Capabilities**
- **Paper Search & Analysis**: Find and analyze academic papers by keywords, topics, or authors
- **Author Profiling**: Detailed author information including publications, citations, and collaboration networks
- **Citation Analysis**: Explore citation relationships and academic impact
- **Research Trends**: Identify trending papers and emerging research areas
- **Keyword Analysis**: Extract and analyze popular research keywords

### 🤖 **AI-Powered Features**
- Intent recognition and query understanding
- Structured data extraction and processing
- Natural language response generation
- Academic writing assistance
- Research recommendation system

### 🔧 **Technical Architecture**
- **FastAPI** backend with RESTful APIs
- **MCP (Model Control Protocol)** for external service integration
- **Together.ai** LLM integration for advanced language processing
- Modular design with separate intent analysis and response integration
- Comprehensive logging and error handling

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Intent Analyzer │    │ Response        │
│                 │────│                  │────│ Integrator      │
│  - Chat API     │    │  - Query Analysis│    │ - Data Processing│
│  - Conversation │    │  - Intent        │    │ - LLM Response  │
│    Management   │    │    Classification│    │   Generation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Server    │    │   LLM Service    │    │   Data Layer    │
│                 │    │                  │    │                 │
│  - Academic     │    │  - Together.ai   │    │  - Conversation │
│    Data Access  │    │    Integration   │    │    Storage      │
│  - Paper Search │    │  - Response      │    │  - Message      │
│  - Author Info  │    │    Generation    │    │    History      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation

### Prerequisites
- Python 3.10+
- Virtual environment (recommended)
- Together.ai API key

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/ivan-xin/openresearch-agent.git
cd openresearch-agent
```

2. **Create and activate virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
cd ai-agent
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the `ai-agent` directory:
```env
# Together.ai Configuration
TOGETHER_API_KEY=your_together_ai_api_key
TOGETHER_MODEL=Qwen/Qwen2.5-VL-72B-Instruct

# Application Configuration
APP_NAME=OpenResearch Agent
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
MCP_SERVER_TIMEOUT=60
```

5. **Start the application**
```bash
python main.py
```

The application will be available at `http://localhost:8000`

## API Documentation

### Endpoints

#### Chat API
- **POST** `/api/v1/chat` - Send a chat message
- **POST** `/api/v2/chat` - Enhanced chat with improved features

#### Conversation Management
- **GET** `/api/v1/conversations` - List conversations
- **POST** `/api/v1/conversations` - Create new conversation
- **GET** `/api/v1/conversations/{id}` - Get conversation details

### Example Usage

#### Chat Request
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find papers about machine learning in computer vision",
    "user_id": "user123",
    "conversation_id": null
  }'
```

#### Response
```json
{
  "message": "I found several relevant papers on machine learning in computer vision...",
  "conversation_id": "conv_456",
  "query_id": "query_789",
  "metadata": {
    "intent_type": "search_papers",
    "confidence": 0.95,
    "processing_time": 2.3
  }
}
```

## Supported Query Types

### 📄 Paper-Related Queries
- "Find papers about deep learning"
- "Search for recent papers on neural networks"
- "Show me papers by [author name]"
- "Get details of paper with ID [paper_id]"

### 👨‍🎓 Author-Related Queries
- "Find information about [author name]"
- "Show me [author name]'s publications"
- "Get author details for [author name]"

### 📈 Trend Analysis
- "What are the trending papers in AI?"
- "Show me popular keywords in machine learning"
- "What are the research trends in computer vision?"

### 🔗 Citation Analysis
- "Show citation network for [paper title]"
- "Analyze citations for paper ID [paper_id]"

## Development

### Project Structure
```
ai-agent/
├── api/                    # API routes and handlers
│   ├── v1/                # Version 1 API
│   └── v2/                # Version 2 API
├── core/                  # Core business logic
│   ├── intent_analyzer.py # Query intent analysis
│   └── response_integrator.py # Response generation
├── configs/               # Configuration files
├── models/                # Data models
├── services/              # Business services
├── utils/                 # Utility functions
└── main.py               # Application entry point
```

### Key Components

#### Intent Analyzer
- Analyzes user queries to determine intent
- Supports multiple intent types (search, analysis, trends)
- Provides confidence scoring and parameter extraction

#### Response Integrator
- Processes execution results from MCP services
- Generates structured and natural language responses
- Provides insights and recommendations

## Deployment

### Production Configuration
- Set `DEBUG=false` in environment
- Configure proper logging levels
- Set up reverse proxy (nginx/Apache)
- Enable HTTPS
- Configure monitoring and alerting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive tests for new features
- Update documentation for API changes
- Use type hints for better code clarity

### Common Issues

1. **Service won't start**
   - Check if port 8000 is available
   - Verify Together.ai API key is set
   - Check logs: `sudo journalctl -u ai-agent`

2. **MCP Server connection issues**
   - Ensure openresearch-mcp-server is properly installed
   - Check MCP configuration in `.env`
   - Verify Python paths in MCP config

3. **Permission errors (Production)**
   - Run deployment script with sudo
   - Check file ownership: `ls -la ai-agent/`

4. **Database connection issues**
   - Set `DB_SKIP_IN_DEV=true` for development
   - Configure database credentials properly


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Together.ai](https://together.ai) for LLM services
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation

## Support

For support and questions:
- Create an issue on GitHub
- Check the [documentation](docs/)
- Review the API documentation at `/docs` when running locally

## Roadmap

- [ ] Enhanced citation network visualization
- [ ] Research collaboration analysis
- [ ] Multi-language support
- [ ] Advanced filtering and search options
- [ ] Integration with more academic databases
- [ ] Real-time research trend monitoring
- [ ] Academic writing assistance tools

---

**OpenResearch Agent** - Empowering academic research through intelligent AI assistance.
