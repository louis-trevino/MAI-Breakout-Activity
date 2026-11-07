# MAI Breakout Activity

Team 31

## Employee Onboarding Agent

An Agent where new employees ask questions about the organization. A LangGraph agent retrieves answers from `kb_employee_sample_01.json` (hybrid BM25 + vector RAG over ChromaDB) and replies with up to 5 citations. It uses the OpenAI API (`gpt-4.1-mini` and `text-embedding-3-small`).

See [docs/DESIGN.md](docs/DESIGN.md) for the architecture.

### Setup (Windows)

1. Add your OpenAI API key:

   ```powershell
   copy .env.example .env
   # then edit .env and set OPENAI_API_KEY=sk-...
   ```

   `.env` is git-ignored. Never commit your key.

2. Install the Python dependencies into the virtual environment:

   ```powershell
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the app:

   ```powershell
   streamlit run app.py
   ```

The first run embeds the 22 published KB entries (a fraction of a cent) and saves the index in `.chroma/`. The index is rebuilt only when the KB or the embedding model changes.

### Tests

```powershell
python -m unittest discover -s tests -v
```

The citation tests run offline. The retrieval tests need `OPENAI_API_KEY` and are skipped without it.

### Evaluation

```powershell
python eval/run_eval.py retrieval -v   # vector vs hybrid retrieval, threshold sweep (embeddings only)
python eval/run_eval.py e2e            # full agent -> eval/report_e2e.md
```

### Project layout

```
app.py              Streamlit UI
config.py           Settings (env vars / .env)
agent/graph.py      LangGraph agent: condense → retrieve → relevance → generate / fallback
agent/retriever.py  KB loading, Chroma + BM25 indexing, hybrid search
agent/prompts.py    Prompt templates
eval/               Evaluation set and harness
docs/DESIGN.md      Design document
tests/              Retrieval and citation tests
```
