# Usage Examples - Regulation Navigator MVP

Complete examples for using the Regulation Navigator API with various tools and languages.

## Table of Contents
1. [cURL Examples](#curl-examples)
2. [Python Client](#python-client)
3. [JavaScript/TypeScript](#javascripttypescript)
4. [Bash Scripts](#bash-scripts)
5. [Common Use Cases](#common-use-cases)
6. [Error Handling](#error-handling)

## cURL Examples

### Basic Setup
```bash
# Set API endpoint as variable
API_URL="http://localhost:8000"

# Or for production
API_URL="https://regnav-mvp.azurewebsites.net"
```

### Health Check
```bash
curl -X GET "${API_URL}/health"

# Response:
# {"status":"ok"}
```

### Simple Question
```bash
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is GDPR?",
    "top_k": 3
  }'
```

### Question with Custom Parameters
```bash
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the requirements for data processing consent?",
    "top_k": 5
  }'

# Response:
# {
#   "answer": "Data processing consent must be...",
#   "citations": [
#     {"doc": "Regulation (EU) 2016/679", "section": "Article 4"},
#     {"doc": "Regulation (EU) 2016/679", "section": "Article 7"}
#   ],
#   "scores": [0.65, 0.58, 0.52]
# }
```

### Pretty Print Response
```bash
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is customer due diligence?","top_k":3}' \
  | jq '.'
```

### Save Response to File
```bash
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is AML?","top_k":3}' \
  > response.json

cat response.json
```

### Extract Specific Fields
```bash
# Get only the answer
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is PSD2?","top_k":3}' \
  | jq '.answer'

# Get only citations
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is PSD2?","top_k":3}' \
  | jq '.citations'

# Get only scores
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is PSD2?","top_k":3}' \
  | jq '.scores'
```

### Test with Timeout
```bash
# 20 second timeout
curl --max-time 20 -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}'
```

### Test with Verbose Output
```bash
# See all request/response headers
curl -v -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}'
```

### Test Error Cases
```bash
# Missing question field
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"top_k":3}'

# Response: 422 Unprocessable Entity

# Question too short
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"hi","top_k":3}'

# Response: 422 Unprocessable Entity

# Top_k too large
curl -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":100}'

# Response: 422 Unprocessable Entity
```

## Python Client

### Simple Request
```python
import requests
import json

# Configuration
API_URL = "http://localhost:8000"

# Ask a question
response = requests.post(
    f"{API_URL}/ask",
    json={
        "question": "What is GDPR?",
        "top_k": 3
    }
)

# Check status
if response.status_code == 200:
    data = response.json()
    print(f"Answer: {data['answer']}")
    print(f"Citations: {data['citations']}")
    print(f"Scores: {data['scores']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### With Error Handling
```python
import requests
from requests.exceptions import RequestException, Timeout

API_URL = "http://localhost:8000"

def ask_regulation_navigator(question, top_k=3, timeout=20):
    """
    Ask Regulation Navigator a question.
    
    Args:
        question: The question to ask
        top_k: Number of sources to retrieve (1-10)
        timeout: Request timeout in seconds
    
    Returns:
        dict: Response with answer, citations, scores
    
    Raises:
        ValueError: For invalid input
        RequestException: For network errors
        Timeout: If request exceeds timeout
    """
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question, "top_k": top_k},
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 422:
            raise ValueError(f"Invalid input: {response.text}")
        elif response.status_code == 502:
            raise RequestException("LLM service unavailable")
        else:
            raise RequestException(f"Unexpected response: {response.status_code}")
    
    except Timeout:
        raise Timeout(f"Request exceeded {timeout} seconds")
    except RequestException as e:
        raise RequestException(f"Network error: {e}")

# Usage
try:
    result = ask_regulation_navigator("What is customer due diligence?")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {', '.join([f\"{c['doc']}|{c['section']}\" for c in result['citations']])}")
except ValueError as e:
    print(f"Invalid question: {e}")
except RequestException as e:
    print(f"Request failed: {e}")
```

### Batch Processing
```python
import requests
import time

API_URL = "http://localhost:8000"

questions = [
    "What is GDPR?",
    "What is AML?",
    "What is PSD2?",
    "What is MiFID II?"
]

results = []

for question in questions:
    try:
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question, "top_k": 3},
            timeout=30
        )
        
        if response.status_code == 200:
            results.append({
                "question": question,
                "answer": response.json()["answer"],
                "status": "success"
            })
        else:
            results.append({
                "question": question,
                "error": response.status_code,
                "status": "failed"
            })
        
        # Rate limiting: 1 second between requests
        time.sleep(1)
    
    except Exception as e:
        results.append({
            "question": question,
            "error": str(e),
            "status": "error"
        })

# Display results
for result in results:
    print(f"Q: {result['question']}")
    if result["status"] == "success":
        print(f"A: {result['answer'][:100]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")
    print()
```

### JSON Output
```python
import requests
import json

API_URL = "http://localhost:8000"

# Get response
response = requests.post(
    f"{API_URL}/ask",
    json={"question": "What is GDPR?", "top_k": 3}
)

# Pretty print
print(json.dumps(response.json(), indent=2))

# Save to file
with open("response.json", "w") as f:
    json.dump(response.json(), f, indent=2)
```

## JavaScript/TypeScript

### Basic Fetch
```javascript
const API_URL = "http://localhost:8000";

async function askQuestion(question, top_k = 3) {
    try {
        const response = await fetch(`${API_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                top_k: top_k
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error:", error);
        throw error;
    }
}

// Usage
askQuestion("What is GDPR?").then(data => {
    console.log("Answer:", data.answer);
    console.log("Citations:", data.citations);
    console.log("Scores:", data.scores);
});
```

### With Async/Await
```typescript
interface Citation {
    doc: string;
    section: string;
}

interface RegulationResponse {
    answer: string;
    citations: Citation[];
    scores: number[];
}

async function getComplianceAnswer(
    question: string,
    topK: number = 3
): Promise<RegulationResponse> {
    const response = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: topK })
    });
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
}

// Usage
const result = await getComplianceAnswer("What is customer due diligence?");
console.log(result.answer);
```

## Bash Scripts

### Simple Query Script
```bash
#!/bin/bash

API_URL="http://localhost:8000"

if [ -z "$1" ]; then
    echo "Usage: $0 <question>"
    exit 1
fi

QUESTION="$1"
TOP_K=${2:-3}

curl -s -X POST "${API_URL}/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\":\"${QUESTION}\",\"top_k\":${TOP_K}}" \
    | jq '.'
```

### Save and run
```bash
chmod +x ask.sh
./ask.sh "What is GDPR?"
```

### Batch Query Script
```bash
#!/bin/bash

API_URL="http://localhost:8000"
QUESTIONS_FILE="questions.txt"  # One question per line
OUTPUT_FILE="answers.json"

# Initialize output file
echo "[" > "$OUTPUT_FILE"

# Process each question
while IFS= read -r question; do
    echo "Processing: $question"
    
    response=$(curl -s -X POST "${API_URL}/ask" \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"${question}\",\"top_k\":3}")
    
    echo "$response" | jq ". + {question: \"${question}\"}" >> "$OUTPUT_FILE"
    echo "," >> "$OUTPUT_FILE"
    
    # Rate limiting
    sleep 1
done < "$QUESTIONS_FILE"

# Remove trailing comma and close array
sed -i '$ s/,$//' "$OUTPUT_FILE"
echo "]" >> "$OUTPUT_FILE"

echo "Results saved to $OUTPUT_FILE"
```

### Health Check Script
```bash
#!/bin/bash

API_URL="http://localhost:8000"
TIMEOUT=5

echo "Checking API health..."

response=$(curl -m $TIMEOUT -s -o /dev/null -w "%{http_code}" "${API_URL}/health")

if [ "$response" = "200" ]; then
    echo "✓ API is healthy (HTTP 200)"
    exit 0
else
    echo "✗ API is unhealthy (HTTP $response)"
    exit 1
fi
```

## Common Use Cases

### Finance Compliance Question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the customer due diligence requirements for financial institutions?",
    "top_k": 5
  }'
```

### Data Protection Query
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What constitutes personal data under GDPR and how should it be protected?",
    "top_k": 3
  }'
```

### Payment Services Inquiry
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the rules for payment service providers under PSD2?",
    "top_k": 4
  }'
```

## Error Handling

### Validation Errors (422)
```bash
# Too short question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"hi"}'

# Response: 422 Unprocessable Entity
# Error details in response body explaining validation failure
```

### LLM Unavailable (502)
```bash
# When Azure OpenAI API is unreachable
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}'

# Response: 502 Bad Gateway
# Check Azure OpenAI credentials and connectivity
```

### Timeout (504)
```python
try:
    response = requests.post(
        "http://localhost:8000/ask",
        json={"question": "Complex regulatory question?", "top_k": 5},
        timeout=10  # 10 second timeout
    )
except requests.exceptions.Timeout:
    print("Request timed out - LLM may be slow or overloaded")
```

## Response Parsing Examples

### Extract Answer Only
```bash
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}' \
  | jq -r '.answer'
```

### Extract Source Document Names
```bash
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}' \
  | jq -r '.citations[].doc'
```

### Format as Markdown
```bash
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}' \
  | jq -r '"# Answer\n\n\(.answer)\n\n## Sources\n\n" + 
           (.citations | map("- \(.doc): \(.section)") | join("\n"))'
```

### CSV Export
```bash
curl -s -X POST "${API_URL}/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}' \
  | jq -r '"Question,Answer,Document,Section,Score\n" + 
           ("What is GDPR?," + .answer + "," + 
            (.citations[] | @csv) + "," + .scores[])' \
  > results.csv
```

## Performance Tips

1. **Reuse connections** - Connection pooling for multiple requests
2. **Batch queries** - Group related questions together
3. **Cache results** - Store frequently asked questions
4. **Increase timeout** - Default may be too short for first LLM call
5. **Adjust top_k** - Fewer sources = faster responses

## Troubleshooting Common Issues

### "Connection refused"
- Check if server is running: `curl http://localhost:8000/health`
- Verify port 8000 is accessible
- Check firewall settings

### "408 Request Timeout"
- Increase timeout value in client
- Check if LLM API is slow
- Reduce question complexity

### "422 Unprocessable Entity"  
- Verify question length (5-1000 chars)
- Verify top_k is 1-10
- Check JSON format is valid

### "502 Bad Gateway"
- LLM API is unreachable
- Check Azure OpenAI credentials
- Verify API endpoint is correct
