# Quick Start Guide

Get up and running with the EU Banking Regulator LLM in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- OpenAI API key OR Anthropic API key

## Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/Muthukumar123/reg-nav-mvp.git
cd reg-nav-mvp

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-openai-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# OR for Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
```

## Step 3: Load Sample Data

Seed the database with sample EU banking regulations:

```bash
python -m src.utils.seed_data
```

You should see output like:
```
Starting database seeding...
Ingesting: Capital Requirements Regulation (CRR) - Article 92
✓ Successfully ingested: Capital Requirements Regulation (CRR) - Article 92 (3 chunks)
...
Database seeding completed!
```

## Step 4: Start the API

```bash
python -m src.api.main
```

The API will start on `http://localhost:8000`

Visit `http://localhost:8000/docs` for the interactive API documentation.

## Step 5: Try It Out!

### Option A: Using the Interactive CLI

Open a new terminal and run:

```bash
python cli.py query
```

Ask questions like:
- "What are the minimum capital requirements for EU banks?"
- "What are the GDPR data processing principles?"
- "When is customer due diligence required under AML?"

### Option B: Using the API

```bash
# Query regulations
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the capital requirements for banks?",
    "include_references": true
  }'

# Check compliance
curl -X POST "http://localhost:8000/api/compliance/check" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "We want to process customer data for marketing",
    "detailed_analysis": true
  }'
```

### Option C: Run Examples

```bash
python examples.py
```

This will run several example queries and show you the system in action.

## What's Next?

- 📖 Read the full [README](README.md) for detailed features
- 🔌 Check the [API Documentation](docs/API.md) for all endpoints
- 🚀 See [Deployment Guide](docs/DEPLOYMENT.md) for production deployment
- 📝 Add your own regulatory documents using the ingestion API
- 🔧 Customize the configuration in `.env` file

## Troubleshooting

### "No module named 'XXX'"
```bash
# Ensure you're in the virtual environment
source venv/bin/activate
# Reinstall requirements
pip install -r requirements.txt
```

### "API key not configured"
Check your `.env` file has the correct API key for your chosen provider.

### "ChromaDB error"
The vector database directory is created automatically. If you get errors, try:
```bash
rm -rf data/vector_db
python -m src.utils.seed_data
```

## Example Queries to Try

1. **Capital Requirements**: "What are the Common Equity Tier 1 capital requirements?"
2. **MiFID II**: "What are the requirements for investment firm authorization?"
3. **GDPR**: "What principles must banks follow when processing personal data?"
4. **AML**: "What is enhanced due diligence and when is it required?"
5. **PSD2**: "What is strong customer authentication?"
6. **Remuneration**: "What are the variable remuneration limits for bank staff?"

## Getting Help

- 📚 Check the documentation in the `docs/` folder
- 🐛 Report issues on GitHub
- 💬 Ask questions in the repository discussions

Happy querying! 🎉
