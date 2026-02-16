# Vertiqx AI Calling Agent - Setup Instructions

## Overview
This guide will help you set up and run the Vertiqx AI Calling Agent system, which provides automated booking, WhatsApp automation, and AI customer support services.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: Minimum 4GB (8GB recommended for better performance)
- **Storage**: At least 2GB free space for models and data

### Required Software
1. **Python 3.7+** - [Download from python.org](https://www.python.org/downloads/)
2. **Ollama CLI** - [Download from ollama.ai](https://ollama.ai/)

## Installation Steps

### Step 1: Install Ollama
1. Download and install Ollama from [ollama.ai](https://ollama.ai/)
2. Verify installation by opening a terminal and running:
   ```bash
   ollama --version
   ```

### Step 2: Install the Required AI Model
1. Install the Gemma 4B model (recommended for this system):
   ```bash
   ollama pull gemma2:4b
   ```
   
   **Alternative models** (if gemma2:4b is not available):
   ```bash
   # Option 1: Gemma 2B (faster, less accurate)
   ollama pull gemma2:2b
   
   # Option 2: Llama 3.1 8B (slower, more accurate)
   ollama pull llama3.1:8b
   
   # Option 3: Phi-3 Mini (good balance)
   ollama pull phi3:mini
   ```

2. Verify the model is installed:
   ```bash
   ollama list
   ```

### Step 3: Start Ollama Service
1. Start the Ollama service:
   ```bash
   ollama serve
   ```
   
   **Note**: Keep this terminal window open while using the AI agent.

### Step 4: Set Up Python Environment
1. Clone or download the project files to your desired directory
2. Navigate to the project directory:
   ```bash
   cd path/to/vertiqx-ai-agent
   ```

3. Create a virtual environment (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\\Scripts\\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 5: Test the Installation
1. Run the comprehensive demo:
   ```bash
   python example_usage_complete.py
   ```

2. If successful, you should see:
   ```
   ✅ System initialized successfully!
   ```

## Configuration

### Model Configuration
If you installed a different model than `gemma2:4b`, update the model name in the agent files:

1. Open `vertiqx_enhanced_agent.py`
2. Find the line:
   ```python
   self.model_name = "gemma2:4b"
   ```
3. Change it to your installed model:
   ```python
   self.model_name = "your-model-name"  # e.g., "phi3:mini"
   ```

### Database Configuration
The system uses SQLite by default. The database file (`vertiqx_bookings.db`) will be created automatically in the project directory.

## Usage

### Running the Enhanced Agent
```bash
python vertiqx_enhanced_agent.py
```

### Running the Complete Demo
```bash
# Automated demo
python example_usage_complete.py

# Interactive demo
python example_usage_complete.py interactive
```

### Running the Basic Agent
```bash
python vertiqx_ai_agent.py
```

## Features Overview

### 🤖 AI Agent Capabilities
- **Natural Language Processing**: Understands customer inquiries in natural language
- **Intent Detection**: Automatically detects booking, cancellation, and service inquiries
- **Customer Information Extraction**: Extracts names, phone numbers, and email addresses
- **Conversation Management**: Maintains context throughout conversations

### 📅 Booking Management
- **Service Types**: Car detailing, WhatsApp automation, AI customer support
- **Booking Creation**: Automated booking with customer information
- **Booking Cancellation**: Easy cancellation process
- **Booking Reports**: Generate summaries and reports

### 💾 Data Management
- **SQLite Database**: Reliable local data storage
- **Conversation History**: Automatic saving of all conversations
- **Customer Records**: Persistent customer information storage
- **Booking Analytics**: Track booking patterns and statistics

## Troubleshooting

### Common Issues

#### 1. "Connection refused" or "Ollama not responding"
**Solution**: Ensure Ollama service is running:
```bash
ollama serve
```

#### 2. "Model not found" error
**Solution**: Install the required model:
```bash
ollama pull gemma2:4b
```

#### 3. Python import errors
**Solution**: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

#### 4. Database permission errors
**Solution**: Ensure the project directory has write permissions.

### Performance Optimization

#### For Better Performance:
1. **Use a faster model**: `gemma2:2b` or `phi3:mini`
2. **Increase system RAM**: 8GB+ recommended
3. **Use SSD storage**: Faster model loading

#### For Better Accuracy:
1. **Use a larger model**: `llama3.1:8b` or `gemma2:9b`
2. **Provide more context**: Include detailed service descriptions
3. **Fine-tune prompts**: Customize the system prompts for your specific use case

## File Structure

```
vertiqx-ai-agent/
├── vertiqx_ai_agent.py           # Basic AI agent
├── vertiqx_enhanced_agent.py     # Enhanced agent with booking integration
├── booking_manager.py            # Booking and customer management
├── example_usage_complete.py     # Comprehensive demo and examples
├── requirements.txt              # Python dependencies
├── SETUP_INSTRUCTIONS.md         # This file
├── vertiqx_bookings.db          # SQLite database (created automatically)
└── conversations/               # Saved conversation history (created automatically)
```

## Customization

### Adding New Services
1. Open `booking_manager.py`
2. Find the `get_service_types()` method
3. Add your new service to the list:
   ```python
   def get_service_types(self) -> List[str]:
       return [
           "car detailing",
           "whatsapp automation", 
           "ai customer support",
           "your-new-service"  # Add here
       ]
   ```

### Customizing Agent Responses
1. Open `vertiqx_enhanced_agent.py`
2. Find the `_get_system_prompt()` method
3. Modify the prompt to match your business needs

### Adding New Intent Types
1. Open `vertiqx_enhanced_agent.py`
2. Find the `detect_intent()` method
3. Add new intent detection logic

## Support and Maintenance

### Regular Maintenance
1. **Update models**: Regularly check for model updates
   ```bash
   ollama pull gemma2:4b
   ```

2. **Backup database**: Regularly backup `vertiqx_bookings.db`

3. **Clean conversation history**: Periodically clean old conversation files

### Getting Help
- Check the troubleshooting section above
- Review the example usage in `example_usage_complete.py`
- Examine the conversation logs for debugging

## Security Considerations

### Data Protection
- Customer data is stored locally in SQLite
- No data is sent to external services (except Ollama locally)
- Conversation history includes sensitive information - secure appropriately

### Recommended Security Measures
1. **File Permissions**: Restrict access to database and conversation files
2. **Regular Backups**: Backup customer data regularly
3. **Access Control**: Limit who can run the agent system
4. **Log Monitoring**: Monitor conversation logs for sensitive information

## Production Deployment

### For Production Use:
1. **Use a dedicated server**: Don't run on personal computers
2. **Set up monitoring**: Monitor system performance and errors
3. **Implement logging**: Set up comprehensive logging
4. **Regular updates**: Keep Ollama and models updated
5. **Backup strategy**: Implement automated backups
6. **Load testing**: Test with expected conversation volumes

### Scaling Considerations:
- **Multiple instances**: Run multiple agent instances for high volume
- **Database optimization**: Consider PostgreSQL for high-volume scenarios
- **Model optimization**: Use quantized models for faster inference
- **Caching**: Implement response caching for common queries

---

## Quick Start Summary

1. **Install Ollama**: Download from ollama.ai
2. **Install Model**: `ollama pull gemma2:4b`
3. **Start Service**: `ollama serve`
4. **Install Dependencies**: `pip install -r requirements.txt`
5. **Run Demo**: `python example_usage_complete.py`

🎉 **You're ready to use the Vertiqx AI Calling Agent!**