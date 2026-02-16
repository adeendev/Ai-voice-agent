# Vertiqx AI Calling Agent
$ python api_server.py --host 0.0.0.0 --port 8000

A sophisticated AI-powered calling agent system designed for Vertiqx, featuring intelligent conversation handling, booking management, and seamless integration with Ollama for local LLM processing.

## 🚀 Features

### Core Capabilities
- **Intelligent Conversation Management**: Natural language processing with context awareness
- **Booking System**: Complete booking lifecycle management (create, update, cancel, track)
- **Customer Management**: Automated customer information extraction and storage
- **Service Detection**: AI-powered service type identification from customer messages
- **Multi-Intent Handling**: Supports booking, cancellation, service inquiries, and general conversations

### AI Integration
- **Ollama Integration**: Local LLM processing with Gemma2 model
- **Intent Detection**: Automatic classification of customer requests
- **Context Preservation**: Maintains conversation history and context
- **Smart Responses**: Contextually appropriate responses based on conversation flow

### Data Management
- **SQLite Database**: Lightweight, efficient data storage
- **Customer Profiles**: Comprehensive customer information tracking
- **Booking Analytics**: Detailed booking reports and summaries
- **Conversation Logs**: Complete conversation history with JSON export

## 📁 Project Structure

```
Vertiqx-AI-Agent/
├── vertiqx_ai_agent.py          # Core AI agent implementation
├── vertiqx_enhanced_agent.py    # Enhanced agent with advanced features
├── booking_manager.py           # Booking and customer management
├── example_usage_complete.py    # Comprehensive usage examples
├── test_system.py              # System testing and validation
├── requirements.txt            # Python dependencies
├── SETUP_INSTRUCTIONS.md       # Detailed setup guide
└── README.md                   # This file
```

## Services Supported

- Car Detailing and Cleaning
- WhatsApp Automation
- AI Customer Support
- General Business Services

## 🛠️ Quick Start

### Prerequisites
- Python 3.8 or higher
- Ollama installed and running
- 4GB+ RAM (for LLM processing)

### Installation

1. **Clone or download the project files**
   ```bash
   # Ensure all project files are in your working directory
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and setup Ollama**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull gemma3:4b  # Download the AI model
   ```

4. **Test the system**
   ```bash
   python test_system.py
   ```

5. **Run the demo**
   ```bash
   python example_usage_complete.py
   ```

2. **Interact with the assistant**:
   - Say "Hello" to start
   - "Book a car wash at 3 PM tomorrow"
   - "Check my appointments"
   - "Cancel my booking"

## Usage Examples

### Booking a Service
```
User: "I want to book a car wash at 3 PM tomorrow"
Assistant: "Sure! I've booked your Car Wash for 3 PM tomorrow. Can I help with anything else?"
```

### Checking Bookings
```
User: "Do I have any appointments?"
Assistant: "You have the following bookings: Car Wash at 3 PM tomorrow."
```

### Cancelling a Booking
```
User: "Cancel my car wash appointment"
Assistant: "Your Car Wash at 3 PM tomorrow has been cancelled. Anything else I can assist you with?"
```

## Architecture

### Core Components

1. **main.py**: Main application orchestrator
2. **ai_assistant.py**: Natural language processing and response generation
3. **booking_database.py**: SQLite database operations
4. **audio_processor.py**: Speech-to-text and text-to-speech

### Database Schema

**Bookings Table**:
- id (Primary Key)
- customer_name
- service_name
- appointment_time
- appointment_date
- status (active/cancelled)
- created_at
- notes

**Services Table**:
- id (Primary Key)
- name
- duration_minutes
- price
- description

## Configuration

### Audio Settings
- Microphone calibration on startup
- Configurable speech recognition timeout
- Adjustable TTS voice and speed

### Business Settings
- Business hours: 9 AM to 6 PM, Monday to Saturday
- Service duration and pricing in database
- Booking conflict detection

## Integration with Local LLMs

### Using Ollama (Recommended)
```python
from ollama import Ollama

ollama = Ollama()
response = ollama.generate(
    model="phi3",
    prompt=f"{system_prompt}\\nUser: {user_input}\\nAI:"
)
```

### Using Hugging Face Transformers
```python
from transformers import pipeline

generator = pipeline("text-generation", model="microsoft/DialoGPT-medium")
response = generator(f"User: {user_input}\\nAI:", max_length=150)
```

## Extending the System

### Adding New Services
```python
# Add to database
db.connection.execute('''
    INSERT INTO services (name, duration_minutes, price, description)
    VALUES (?, ?, ?, ?)
''', ("New Service", 90, 75.00, "Description"))
```

### Custom Intent Recognition
```python
# Extend _analyze_intent method in ai_assistant.py
def _analyze_intent(self, user_input):
    # Add new intent patterns
    if "custom_pattern" in user_input.lower():
        return {"type": "custom_intent", "confidence": 0.8}
```

### Web Interface (Optional)
Create a Flask web interface for browser-based interaction:
```python
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
assistant = AIBookingAssistant(database)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    response = assistant.process_request(user_input)
    return jsonify({'response': response})
```

## Troubleshooting

### Audio Issues
- **Microphone not detected**: Check audio device permissions
- **Poor recognition**: Calibrate microphone in quiet environment
- **TTS not working**: Verify pyttsx3 installation

### Database Issues
- **Database locked**: Ensure only one instance is running
- **Missing tables**: Delete bookings.db and restart

### Performance Optimization
- Use smaller LLM models (TinyLLaMA, Phi-3-mini)
- Limit conversation context to last 10 messages
- Use local STT models for offline operation

## Development

### Running Tests
```bash
pytest tests/
```

### Adding Features
1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code documentation
3. Create an issue with detailed description

---

**Built for Vertiqx Services** - Streamlining local business operations with AI.