# Path of Exile 2 Build Assistant

A comprehensive build guide extraction and recommendation system for Path of Exile 2, featuring LLM-powered data extraction, quality validation, and multiple user interfaces.

## 🎮 Features

- **Automated Build Extraction**: Scrapes and extracts build guides from Maxroll.gg and Mobalytics.gg using LLM (Ollama)
- **Quality Validation**: Confidence scoring system validates extracted data against ground truth
- **Learning System**: Continuously improves data quality by learning new skills and passives
- **Multiple Interfaces**: 
  - Telegram Bot with pagination
  - Flask Web UI for visualization
  - Desktop GUI (Tkinter)
- **Smart Recommendations**: Combines data quality (70%) and popularity (30%) for scoring

## 📋 Prerequisites

- Python 3.8+
- Ollama with Mistral model installed
- Google Custom Search API credentials (optional, for online updates)
- Telegram Bot Token (optional, for bot interface)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd poe2_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Ollama and Mistral model**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull mistral
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## ⚙️ Configuration

Create a `.env` file with the following:

```env
# Google Search API (for build fetching)
GOOGLE_SEARCH_API_KEY=your_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_engine_id_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_token_here

# Ollama Configuration
OLLAMA_MODEL=mistral
OLLAMA_TEMPERATURE=0.1
OLLAMA_TIMEOUT=120.0

# Logging
LOG_LEVEL=INFO
```

## 📖 Usage

### 1. Initialize Ground Truth
```bash
python poe2_ground_truth_manager.py
```

### 2. Fetch Builds Online
```bash
python update_builds_online.py --force
```

### 3. Run Learning System
```bash
python learning_system.py learn
python learning_system.py stats
```

### 4. Start Telegram Bot
```bash
python bot_paginated.py
```

### 5. Launch Web Interface
```bash
python poe2_web_editor.py
```

### 6. Batch Extract Builds
```bash
python batch_extractor.py
```

## 📁 Project Structure

```
poe2_app/
├── config.py                    # Central configuration
├── poe2_schema.py              # Pydantic data models
├── poe2_parser.py              # Build parsing and validation
├── poe2_fetcher.py             # Online build fetching
├── poe2_data_ref.py            # Ground truth validation
├── poe2_ground_truth_manager.py # GT management
├── learning_system.py          # Continuous learning
├── llm_extractor_v2.py         # LLM extraction logic
├── batch_extractor.py          # Batch processing
├── bot_paginated.py            # Telegram bot
├── poe2_web_editor.py          # Flask web UI
├── poe2_app_builder.py         # Tkinter GUI
├── requirements.txt            # Dependencies
├── .env                        # Environment variables
└── data/                       # Data files
    ├── poe2_builds.json
    ├── poe2_ref_data.json
    └── learning_stats.json
```

## 🔧 How It Works

### Data Pipeline

1. **Extraction**: `poe2_fetcher.py` searches Google for builds and scrapes content
2. **LLM Processing**: `llm_extractor_v2.py` uses Ollama/Mistral to extract structured data
3. **Validation**: `poe2_data_ref.py` validates against known skills/passives
4. **Scoring**: `poe2_parser.py` calculates confidence and recommendation scores
5. **Learning**: `learning_system.py` updates ground truth with new discoveries
6. **Storage**: Builds stored in `poe2_builds.json`

### Quality Metrics

- **Confidence Score**: Percentage of extracted items matching ground truth
- **Recommendation Score**: Weighted combination of confidence (70%) and reputation (30%)
- **Minimum Thresholds**: 
  - 40% confidence
  - 3+ unique skills

## 🤖 Telegram Bot Commands

- `/start` - Welcome message and instructions
- `/classes` - List all available classes
- `/build <class>` - View builds for a specific class
- Navigation: Use inline buttons to browse builds

## 🌐 Web Interface

Access at `http://localhost:5000` after running `poe2_web_editor.py`

- Select class from dropdown
- View builds organized by level ranges
- See skills and passive tree progression

## 🧪 Testing

```bash
# Validate all builds
python poe2_parser.py

# Check ground truth stats
python learning_system.py stats

# Test LLM extraction
python llm_extractor_v2.py
```

## 📊 Data Files

- `poe2_builds.json`: Extracted build data organized by class
- `poe2_ref_data.json`: Ground truth (known skills and passives)
- `learning_stats.json`: Learning system statistics
- `last_fetch.txt`: Timestamp of last online update

## 🛠️ Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# Windows: Check Task Manager
# Linux/Mac: systemctl restart ollama
```

### Google API Quota Exceeded
- Wait 24 hours or use `--force` flag sparingly
- Consider using cached builds

### Low Confidence Scores
- Run learning system: `python learning_system.py learn`
- Update ground truth manually in `poe2_ref_data.json`

## 🚧 Known Limitations

- Some classes (Druid, Duelist, etc.) skipped due to lack of data
- LLM extraction quality depends on source website structure
- Requires active internet for build updates
- Ground truth requires periodic manual curation

## 📝 Future Improvements

- [ ] Add unit tests
- [ ] Implement caching layer
- [ ] Support more build sources
- [ ] Add build comparison feature
- [ ] Export builds to PoB format
- [ ] Add equipment recommendations
- [ ] Implement user ratings system

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is for educational purposes. Path of Exile 2 is owned by Grinding Gear Games.

## 🙏 Acknowledgments

- Build data from Maxroll.gg and Mobalytics.gg
- Skill/passive data from poe2db.tw
- Powered by Ollama and Mistral LLM
