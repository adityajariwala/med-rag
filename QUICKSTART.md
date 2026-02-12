# Med-RAG Quick Start Guide

## 🚀 5-Minute Setup

### 1. Environment Setup (First Time Only)

```bash
# Navigate to project
cd /Users/adityajariwala/PyCharmMiscProject/med-rag

# Activate virtual environment
pyenv local med-rag  # or: source .venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt
```

### 2. Configure Environment Variables (First Time Only)

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENROUTER_API_KEY, ENTREZ_EMAIL
# Optional: ENTREZ_API_KEY (recommended for higher rate limits)
```

**Where to get keys:**
- OpenRouter API key: https://openrouter.ai/
- NCBI API key: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/

### 3. Start the Application

```bash
# Option A: Start everything with one command (recommended)
./scripts/start_dev.sh

# Option B: Start manually
# Terminal 1:
uvicorn src.api:app --reload

# Terminal 2:
streamlit run src/app.py
```

### 4. Access the Application

- **Streamlit UI** (recommended): http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

---

## 📖 Common Commands

### Development
```bash
# Start both API and UI
./scripts/start_dev.sh

# Start API only
uvicorn src.api:app --reload

# Start Streamlit only
streamlit run src/app.py

# Test the API
python scripts/test_api.py
```

### Maintenance
```bash
# Clear cache (forces fresh PubMed fetch)
rm data/raw/pubmed_cache.json

# Check environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OpenRouter:', os.getenv('OPENROUTER_API_KEY')[:10]+'...'); print('Entrez:', os.getenv('ENTREZ_EMAIL'))"

# Verify installation
python -c "from Bio import Entrez; from sentence_transformers import SentenceTransformer; print('All imports OK')"
```

### Testing
```bash
# Run tests
pytest tests/ -v

# Test API health
curl http://localhost:8000/health

# Test query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the benefits of statins?"}'
```

---

## 🎯 Quick Examples

### Using the Streamlit UI

1. Open http://localhost:8501
2. Click an example question button or type your own
3. Click "Submit"
4. View answer, evidence, and metrics

### Using the API Directly

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "What are the cardiovascular effects of GLP-1 agonists?"}
)

data = response.json()
print(data["answer"]["answer_summary"])
```

### Using curl

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What evidence exists for aspirin in primary prevention?"
  }' | jq
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'Bio'"
```bash
# Ensure you're in the right environment
pyenv local med-rag
python -c "from Bio import Entrez; print('OK')"
```

### "Missing required environment variables"
```bash
# Check your .env file
cat .env

# Ensure it has all required keys from .env.example
diff .env .env.example
```

### "API index is not ready"
Wait a few seconds for the index to build on first startup. Check logs for progress.

### "Cache format error"
```bash
# Delete old cache
rm data/raw/pubmed_cache.json

# Restart API (will rebuild cache)
```

### Slow startup
First run downloads PubMedBERT model (~400MB) and fetches PubMed data. Subsequent runs use cache.

---

## 📁 Project Structure

```
med-rag/
├── src/
│   ├── api.py           # FastAPI backend
│   ├── app.py           # Streamlit frontend
│   ├── ingestion.py     # PubMed retrieval
│   ├── embeddings.py    # PubMedBERT embeddings
│   ├── vector_store.py  # FAISS search
│   └── llm.py           # LLM generation
├── scripts/
│   ├── start_dev.sh     # Start both services
│   └── test_api.py      # API testing
├── data/raw/            # PubMed cache
├── requirements.txt     # Dependencies
├── .env                 # Your API keys (not in git)
└── .env.example         # Template

```

---

## ⚙️ Configuration Options

Edit `.env` to customize:

```bash
# Change default PubMed query
PUBMED_DEFAULT_QUERY=diabetes treatment outcomes

# Use different LLM model
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Change API URL (for Streamlit)
API_URL=http://localhost:8000
```

---

## 🎨 Features

### Streamlit UI Features
- ✅ Interactive question input
- ✅ Example question buttons
- ✅ API health status indicator
- ✅ Metrics dashboard (confidence, recall, faithfulness)
- ✅ Expandable evidence sections
- ✅ Clickable PubMed links
- ✅ Debug panel with raw JSON
- ✅ Error handling with helpful messages

### API Features
- ✅ RESTful endpoints
- ✅ OpenAPI/Swagger docs
- ✅ Health check endpoint
- ✅ Pydantic validation
- ✅ Structured error responses
- ✅ Comprehensive logging

---

## 📚 Documentation

- **README.md** - Full documentation
- **CHANGELOG.md** - All changes and improvements
- **FIXES_SUMMARY.md** - Detailed fix explanations
- **QUICKSTART.md** - This file!

---

## 🔗 Useful Links

- API Docs: http://localhost:8000/docs
- Streamlit UI: http://localhost:8501
- OpenRouter: https://openrouter.ai/
- PubMed: https://pubmed.ncbi.nlm.nih.gov/
- PubMedBERT: https://huggingface.co/pritamdeka/S-PubMedBert-MS-MARCO

---

## ⚠️ Important Notes

1. **This is a research prototype** - not for clinical use
2. **First run is slow** - downloads model and fetches data
3. **Subsequent runs are fast** - uses cached data
4. **Rate limits apply** - use NCBI API key for higher limits
5. **Answers are grounded** - but verify with medical professionals

---

## 🎓 Next Steps

1. Try the example questions in the Streamlit UI
2. Experiment with different queries
3. Check the evaluation metrics
4. Review the retrieved evidence
5. Explore the API docs at /docs

---

**Need help?** Check:
1. README.md for full documentation
2. TROUBLESHOOTING section in README
3. Logs in the terminal for error details
4. FIXES_SUMMARY.md for common issues

**Happy querying! 🏥**
