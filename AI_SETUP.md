# AI Cover Letter Generation Setup

Your Job Automata now supports **AI-generated cover letters** using Google's Gemini Flash. Each cover letter is personalized to the company using their actual description and your full resume.

## Quick Setup (2 minutes)

### 1. Install Dependencies
```bash
make install
```
Or manually:
```bash
pip install google-generativeai python-dotenv
```

### 2. Get a Gemini API Key
- Visit: https://aistudio.google.com/apikey
- Click "Create API Key"
- Copy the key

### 3. Create `.env` File
```bash
# Copy the example
cp .env.example .env

# Edit .env and add your key
echo "GEMINI_API_KEY=your_actual_key_here" > .env
```

Or manually create `.env`:
```
GEMINI_API_KEY=sk-...your-key-here...
```

### 4. Test It
```bash
python3 cover_letter_ai.py
```

You should see output like:
```
2026-04-26 10:15:30 - INFO - Generated AI cover letter for Anthropic (456 chars)
============================================================
Generated Cover Letter for Anthropic
============================================================

I'm writing to express my strong interest in joining Anthropic...
```

## How It Works

### AI Generation (Default)
If `GEMINI_API_KEY` is set in `.env`:
1. Loads your full resume from `cv.md`
2. Fetches company description (scraped from their website)
3. Calls Gemini Flash with a custom prompt
4. Generates a 2-3 paragraph, 150-200 word personalized letter
5. Unique per company (not templated)

### Fallback: Templates
If AI is disabled or fails:
- Falls back to category-based templates
- Same behavior as before

## Usage

### Generate Previews
```bash
make test-letters
```
Shows AI-generated letters for sample companies.

### Dry Run with AI
```bash
make dry-run
```
Generates AI cover letters for all companies in your CSV (doesn't submit).

### Apply with AI
```bash
make apply
```
Submits applications using AI-generated cover letters.

## Example: AI vs Templates

### Template-Based (Old)
```
With deep expertise in machine learning and inference optimization, 
I'm eager to join Anthropic and work on cutting-edge AI solutions.
```
Same for all ML companies 

### AI-Generated (New)
```
I'm impressed by Anthropic's commitment to building reliable, interpretable, 
and steerable AI systems. Your focus on safety aligns perfectly with my research 
in inference optimization and robust model design. I'm excited to contribute to 
making AI more trustworthy and beneficial.
```
Unique to each company 

## Configuration

### Change Model
In `cover_letter_ai.py` line 106, change:
```python
model = genai.GenerativeModel('gemini-2.0-flash')
```

Available models:
- `gemini-2.0-flash` (recommended - fast, cheap)
- `gemini-1.5-pro` (slower, more capable)
- `gemini-1.5-flash` (older version)

### Adjust Temperature (Creativity)
In `cover_letter_ai.py` line 114:
```python
generation_config=genai.types.GenerationConfig(
 temperature=0.7, # 0.0 = deterministic, 1.0 = random
 max_output_tokens=500,
 top_p=0.9,
)
```

## Notes

- **Cost**: Gemini Flash is very cheap (~$0.01 per 100 cover letters)
- **API Key Security**: `.env` is in `.gitignore` - never commit it
- **Fallback**: If API fails, automatically falls back to templates
- **Logging**: Check logs to see which method was used: `grep "AI generation\|template" *.log`

## Troubleshooting

### "GEMINI_API_KEY environment variable not set"
```bash
# Create .env with your key
echo "GEMINI_API_KEY=your_key_here" > .env

# Verify
cat .env
```

### "google-generativeai not installed"
```bash
pip install google-generativeai
```

### API call fails
```bash
# Check if API key is valid at https://aistudio.google.com/apikey
# Increase max_output_tokens if letters are truncated
# Try the older gemini-1.5-flash model if 2.0-flash times out
```

### Want to use templates instead?
Just don't create a `.env` file, or set it empty. The system will automatically fall back.

## What Gets Sent

**Company Description** (scraped from website):
```
Anthropic is an AI safety and research company that's working to build 
reliable, interpretable, and steerable AI systems.
```

**Your Resume** (from cv.md):
```
Full 150+ line resume with projects, experience, skills, etc.
```

**Prompt** (sent to Gemini):
```
"Write a 2-3 paragraph cover letter for [Company] in [Category].
They focus on [Description]. Highlight these skills: [Skills].
Recent projects: [Projects]..."
```

**Result**: A unique, personalized cover letter per company.

---

**Need help?** Check the main [README.md](README.md) or run `make help`.
