# Resume Scanner

Rule-based resume scoring from JSON knowledge bases, optional second opinion via **Ollama** (local LLM).


Uses Software Engineering as default career
```bash
python main.py samples/sample_resume.txt
```

Other careers use `--career` then list the career from kb:

```bash
python main.py samples/sample_resume.txt --career data_science
```

List careers in kb:

```bash
python main.py --list-careers
```

## Ollama (`--use-llm`)

For LLM Block

1. Install **Ollama**: [ollama.com](https://ollama.com) — run the installer and start the app.
2. Pull the default model once:
   ```bash
   ollama pull llama3.2
   ```
3. Run:
   ```bash
   python main.py samples/sample_resume.txt --use-llm
   ```
