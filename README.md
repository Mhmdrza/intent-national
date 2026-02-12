# Propaganda and Cognitive Warfare Analysis Tool

This repository contains the Propaganda and Cognitive Warfare Analysis Tool designed to analyze and evaluate various propaganda techniques and cognitive warfare strategies.

## Architecture

The project is separated into two main components:

1. **Data Pipeline** (Python): Scrapes RSS feeds, analyzes content with AI, and processes data
2. **UI Application** (Next.js): Modern web interface displaying analysis results with Persian Jalali timestamps

## Features

- **RSS Feed Scraping**: Automated collection of content from configured RSS sources
- **AI-Powered Analysis**: Evaluates urgency scores, emotional triggers, and cognitive warfare tactics
- **Persian Jalali Calendar**: Displays last updated timestamps in Persian calendar format
- **Real-time Data Updates**: Separation of data pipeline from UI allows independent updates
- **Responsive Design**: Mobile-friendly interface with RTL support for Persian content

## Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Mhmdrza/intent-national.git
cd intent-national
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

## Usage

### Running the Data Pipeline

1. **Scrape RSS feeds**:
```bash
python rss_scraper.py
```

2. **Analyze content with AI**:
```bash
python ai_analyzer.py
```

3. **Process data for UI**:
```bash
python pipeline/process_data.py
```

### Running the Next.js UI

1. **Development mode**:
```bash
npm run dev
```

2. **Production build**:
```bash
npm run build
npm start
```

The UI will be available at `http://localhost:3000`

## Project Structure

```
├── pipeline/           # Data processing pipeline
│   └── process_data.py # Transforms raw data into UI-ready format
├── app/               # Next.js application
│   ├── page.tsx       # Main page component
│   ├── layout.tsx     # Root layout
│   └── api/           # API routes
├── components/        # React components
├── types/            # TypeScript type definitions
├── data/             # Raw data storage
├── public/           # Static assets and processed data
├── rss_scraper.py    # RSS feed scraper
├── ai_analyzer.py    # AI content analyzer
└── generate_ui.py    # Legacy HTML generator (deprecated)
```

## Data Flow

1. `rss_scraper.py` → Fetches content from RSS feeds → `data/videos.json`
2. `ai_analyzer.py` → Analyzes content → Updates `data/videos.json`
3. `pipeline/process_data.py` → Processes data → `public/data/processed.json`
4. Next.js UI → Fetches from API → Displays analysis results

## API Endpoints

- `GET /api/data` - Returns processed analysis data with Persian Jalali timestamp

## Contribution

Contributions are welcome! Please submit a pull request or open an issue to discuss changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
