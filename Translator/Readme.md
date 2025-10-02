# German-English Translation and Vocabulary Learning System

A comprehensive Python-based system for capturing, translating, and learning German text through OCR, featuring real-time translation, vocabulary training, and database management.

## Overview

This system consists of multiple integrated tools that work together to:
- Capture text from screen areas using OCR
- Translate German text to English using multiple sources (database, DeepL API, manual input)
- Clean and process captured text to remove duplicates and artifacts
- Analyze word frequency for learning prioritization
- Provide interactive vocabulary training
- Maintain a translation database for continuous improvement

## Project Structure

### Core Files

| File | Description |
|------|-------------|
| `ocr_recorder.py` | Basic OCR screen capture tool for text extraction |
| `ocr_translator.py` | Advanced OCR with real-time German-to-English translation |
| `word_translate.py` | Batch translation tool using DeepL API and database lookup |
| `word_frequency.py` | Analyzes word frequency from session files and generates CSV data |
| `word_clean.py` | Cleans OCR artifacts, duplicates, and incomplete sentences |
| `word_vocabulary_trainer.py` | Interactive vocabulary trainer for learning words |
| `check_db.py` | Database inspection and management tool |

### Configuration Files

| File | Description |
|------|-------------|
| `.env` | Environment variables template (copy to `.env.local`) |
| `.gitignore` | Git ignore patterns for security and cleanup |

### Data Files

| File | Description |
|------|-------------|
| `de-en.sqlite3` | SQLite database containing German-English translations |
| `words.csv` | CSV file with word frequencies and translation data |
| `whitelist.txt` | List of words to exclude from processing and learning |
| `requirements.txt` | Python dependencies and packages |

## Features

### OCR and Translation
- Interactive screen area selection for text capture
- Configurable capture intervals (real-time to periodic)
- Real-time German-to-English translation using multiple sources:
  - Local SQLite database lookup
  - DeepL API translation service
  - Manual translation input
- Enhanced OCR processing for German text with special characters (äöüÄÖÜß)
- Optimized for various text backgrounds and formats

### Text Processing
- Automatic duplicate removal and session cleaning
- OCR artifact cleanup (incomplete sentences, garbled text)
- Word frequency analysis for learning prioritization
- Speaker identification and conversation block processing

### Vocabulary Learning
- Interactive training sessions with progress tracking
- Smart word selection based on frequency and learning status
- Integration with translation database for continuous improvement
- Whitelist management for excluding unwanted words

## Requirements

- **Python 3.7+**
- **Tesseract OCR** (download from: https://github.com/UB-Mannheim/tesseract/wiki)
- **DeepL API Key** (for batch translations - get from: https://www.deepl.com/pro-api)
- **Required Python packages** (install with: `pip install -r requirements.txt`)

### Installation Steps

1. **Install Tesseract OCR**:
   - Download and install Tesseract OCR from the official repository
   - Note the installation path for configuration

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**:
   - Copy `.env` to `.env.local`
   - Update the values in `.env.local` with your actual paths and API keys:
     - `TESSERACT_PATH`: Path to your Tesseract installation
     - `DEEPL_API_KEY`: Your DeepL API key
     - `DB_PATH`: Path to your translation database
     - `CSV_PATH`: Path to your words CSV file
     - `WHITELIST_PATH`: Path to your whitelist file

4. **Verify Installation**:
   ```bash
   python check_db.py
   ```

## Complete Workflow

### Phase 1: Text Capture
Choose one of the OCR capture methods:

**Option A: Basic OCR Recording**
```bash
python ocr_recorder.py
```
- Select capture area by clicking corners
- Set capture interval
- Records raw text to session files

**Option B: Real-time Translation**
```bash
python ocr_translator.py
```
- Select capture area by clicking corners
- Set capture interval
- Displays real-time English translations

### Phase 2: Text Processing
Clean and analyze captured text:

```bash
# Clean session files (removes duplicates and artifacts)
python word_clean.py

# Analyze word frequency and generate CSV data
python word_frequency.py
```

### Phase 3: Translation
Translate words using multiple sources:

```bash
# Batch translate words using DeepL API and database
python word_translate.py
```

### Phase 4: Vocabulary Training
Learn new vocabulary interactively:

```bash
# Start vocabulary training session
python word_vocabulary_trainer.py
```

### Phase 5: Database Management
Inspect and manage the translation database:

```bash
# Check database structure and contents
python check_db.py
```

## Detailed Usage Guide

### OCR Screen Recorder (`ocr_recorder.py`)

**Setup Process:**
1. Run the script: `python ocr_recorder.py`
2. Move mouse to top-left corner of desired area, press Enter
3. Move mouse to bottom-right corner, press Enter
4. Set capture interval in seconds
5. Recording starts automatically (Ctrl+C to stop)

**Output:** Creates `session.txt` with raw OCR text and `words.txt` with frequency data.

### OCR Translator (`ocr_translator.py`)

**Enhanced features:**
- Real-time translation display
- Uses both database and CSV translation sources
- Better OCR processing for German text

**Usage:** Same setup process as basic recorder, but displays translated text in real-time.

### Word Cleaning (`word_clean.py`)

**Processes session files to:**
- Remove duplicate conversation blocks
- Clean incomplete sentences from OCR errors
- Preserve speaker identification
- Filter out OCR artifacts

**Usage:** `python word_clean.py` (processes all session files automatically)

### Word Frequency Analysis (`word_frequency.py`)

**Features:**
- Loads and merges with existing word data
- Filters out short words (< 3 characters)
- Respects whitelist exclusions
- Outputs sorted CSV by frequency

**Usage:** `python word_frequency.py` (processes cleaned session files)

### Batch Translation (`word_translate.py`)

**Translation Sources (in order):**
1. Local SQLite database lookup
2. DeepL API translation
3. Manual user input (for untranslatable words)

**Features:**
- Graceful handling of API failures
- Progress saving on interruption (Ctrl+C)
- Automatic whitelist management
- CSV progress persistence

### Vocabulary Trainer (`word_vocabulary_trainer.py`)

**Training Features:**
- Random word selection from untranslated words
- Frequency-based prioritization
- Hint system for difficult words
- Progress tracking and persistence
- Database integration for new translations

**Commands:**
- Type `quit` or `exit` to end session
- Type `hint` to get translation hint
- Press Ctrl+C to save progress and exit

## File Formats

### words.csv Structure
```csv
frequency,word,translation
150,"hallo","hello"
89,"arbeiten","work|to work"
67,"schule","school"
```

### whitelist.txt Format
```
cloud
confidential
der
extern
flow
```

### Database Schema
The `de-en.sqlite3` database contains multiple tables:
- `translation`: Main translation table with scoring
- `simple_translation`: Simplified translation storage
- Additional metadata and configuration tables

## Configuration

### Environment Variables

The system uses environment variables for secure configuration. All sensitive information (API keys, file paths) is loaded from a `.env` file.

**Setup:**
1. Copy `.env` to `.env.local`
2. Update the values in `.env.local` with your actual configuration
3. Never commit `.env.local` to version control

**Available Variables:**
- `TESSERACT_PATH`: Path to Tesseract OCR executable
- `DEEPL_API_KEY`: Your DeepL API key (keep secret!)
- `DEEPL_API_URL`: DeepL API endpoint (usually don't need to change)
- `DB_PATH`: Path to translation database file
- `CSV_PATH`: Path to words CSV file
- `WHITELIST_PATH`: Path to whitelist file
- `DEFAULT_CAPTURE_INTERVAL`: Default OCR capture interval in seconds
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

### Security Features

- **No hardcoded credentials**: All API keys and paths are externalized
- **Environment-based configuration**: Easy deployment across different environments
- **Git integration**: `.gitignore` excludes sensitive files and temporary data
- **Graceful fallbacks**: Scripts work with default values if environment variables are missing

### Manual Configuration (Not Recommended)

If you prefer to hardcode paths (not recommended for security), you can modify the scripts directly:

```python
# In scripts - replace environment loading with direct values
DEEPL_API_KEY = "your-actual-api-key"
DB_PATH = r"C:\path\to\your\database.db"
```

## Tips and Best Practices

### OCR Quality
- Ensure text is clearly visible and well-formatted
- Use consistent font sizes and styles
- Avoid complex layouts or overlapping text
- Higher capture intervals for fast-changing content

### Translation Accuracy
- Review and correct translations in `words.csv`
- Add difficult words to `whitelist.txt` if not needed
- Use manual translation for specialized terminology
- Regularly backup your `words.csv` and database files

### Learning Efficiency
- Focus on high-frequency words first
- Use the vocabulary trainer regularly for retention
- Add domain-specific terms to improve translation accuracy
- Review and update translations as you learn

## Troubleshooting

### Common Issues

**OCR Not Working:**
- Verify Tesseract installation and path
- Check if capture area contains readable text
- Try adjusting capture interval

**Translation Issues:**
- Check DeepL API key validity
- Verify database connection
- Review CSV file format

**Database Errors:**
- Run `check_db.py` to inspect database structure
- Backup database before making manual changes
- Check file permissions

**Import Errors:**
- Install missing packages: `pip install -r requirements.txt`
- Verify Python 3.7+ installation

## Output Files

### Session Files
- `session*.txt` - Raw OCR capture data
- `cleaned_*.txt` - Processed session data (duplicates removed)

### Analysis Files
- `words.csv` - Word frequency and translation data
- `whitelist.txt` - Excluded words list

### Database
- `de-en.sqlite3` - Translation database with scoring and metadata

## Performance Notes

- OCR processing speed depends on capture area size and interval
- DeepL API calls are rate-limited (check your plan limits)
- Large session files may require significant processing time
- Database operations scale with translation table size

## Contributing

When adding new features or fixing issues:
1. Test changes with sample data
2. Update this README with new functionality
3. Maintain backward compatibility
4. Add proper error handling

## License

This project is developed for personal educational use in German language learning.
