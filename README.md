# Resume Ranking System

## Overview
The system provides:
- Detailed match analysis with numerical scores (0-100)
- Justifications for each score category
- Clear explanation of candidate fit

### Score Categories
1. Skills Match:
   - Compares required vs candidate skills
   - Considers skill relevance and proficiency

2. Job Title Match:
   - Evaluates role alignment
   - Considers career progression

3. Experience Match:
   - Compares years and quality of experience
   - Evaluates domain relevance

4. Overall Score:
   - Weighted combination of above scores
   - Detailed justification provided

## Steps
1. Install requirements:  
   ```bash
   pip install streamlit sentence-transformers scikit-learn pandas numpy PyPDF2 python-docx requests
   ```
2. Run app:  
   ```bash
   streamlit run app.py
   ```
3. Components:
   - app.py: Main Streamlit UI
   - extraction.py: File parsing utilities
   - llm_integration.py: Communication with local LLM (Ollama)
   - matching_engine.py: Scoring logic and summarization prompts

## LLM Integration
Uses LMStudio with deepseek-r1-distill-qwen-7b model for:

1. Information Extraction
   - Resume parsing (skills, experience, etc.)
   - Job description requirements
   - Returns structured JSON

2. Match Analysis
   - Computes skill match scores
   - Evaluates experience fit
   - Provides detailed justification

### Response Format
LMStudio responses contain:
```json
{
  "choices": [{
    "text": "...JSON content..."
  }]
}
```

The system extracts the JSON content from the "text" field and processes it.

To connect to a real local LLM (e.g., Ollama):
1. Install and start your Ollama server.
2. Update the stub methods in llm_integration.py to send and receive requests from your local server, e.g.:
   ```python
   response = requests.post("http://localhost:11411/completions", json={"prompt": prompt})
   ```
3. Update any parameters or authentication details as necessary to match your LLM configuration.

### Using Ollama (llama3.2:3b-instruct-fp16)
1. Ensure Ollama is installed and running on localhost:11411.
2. Set model to "llama3.2:3b-instruct-fp16" in llm_integration.py.

## Matching & Scoring Logic
1. **Skills Matching:**
   - Extract skills from both JD and Resume.
   - Use Sentence Transformers to generate embeddings.
   - Compute cosine similarity.
2. **Job Title Matching:**
   - Extract job titles from both documents.
   - Compute similarity via embeddings or fuzzy matching.
3. **Experience Matching:**
   - Extract and compare years of experience.
4. **Score Aggregation:**
   - Define a weighted formula combining skills, job title, and experience match.
   - Tune weights based on importance.

## Extraction & Parsing
1. **File Parsing:**
   - Use PyPDF2 for PDFs.
   - Use python-docx for DOCX files.
   - Implement OCR if necessary for images.
2. **Preprocessing:**
   - Normalize text (remove special characters, whitespace cleanup).

## Candidate Summary Generation
- Utilize LLM to generate a contextual explanation based on extracted data and scores.
- Provide insights on why a candidate is a good or poor match.
- Return as JSON to be displayed in Streamlit UI.

## Match Analysis Display
The system shows:
```
Skill Match Score: XX
[Detailed justification...]

Job Title Match Score: XX  
[Role alignment explanation...]

Experience Match Score: XX
[Experience evaluation...]

Overall Match Score: XX
[Summary of fit...]
```

## Additional Notes
- Adjust weights in matching_engine.py to fine-tune results.
- Ensure Ollama is running locally before testing LLM calls.
- Validate extracted data to prevent parsing errors.

