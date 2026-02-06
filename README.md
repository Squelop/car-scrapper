# Car Market Insights Scraper 🚗

A comprehensive web scraping and data visualization system for Polish car marketplaces. Automatically collects car listings from **Otomoto**, **OLX**, and **Autoplac**, tracks prices over time, and visualizes market trends.

## ✨ Features

- **Multi-Platform Scraping**: Collects data from Otomoto, OLX, and Autoplac
- **Comprehensive Data Collection**: 
  - Brand, model, year, mileage
  - Price, fuel type, engine capacity, power
  - Body type, color, condition (new/used/damaged)
  - Location and listing date
- **Historical Price Tracking**: Monitor how prices change over time
- **Rich Visualizations**:
  - Average price by production year
  - Price vs mileage scatter plot
  - Historical price trends over time
  - Average price by fuel type
- **GitHub Actions Integration**: Automated daily scraping
- **GitHub Pages Deployment**: Static site hosting

## 🏗️ Architecture

This project uses a **Git Scraping** approach:
1. GitHub Actions runs scrapers on a schedule
2. Data is saved to `frontend/public/data/listings.json`
3. Changes are committed back to the repository
4. Frontend (deployed to GitHub Pages) reads the static data file

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Git

## 🚀 Quick Start

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

#### Run Scrapers Locally
```bash
cd backend

# Test mode (scrapes 1 page from each platform)
python cli.py --test

# Scrape specific platform
python cli.py --platform otomoto --url "https://www.otomoto.pl/osobowe" --pages 3

# Use configuration file
python cli.py --config scraper_config.json --pages 2
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### GitHub Deployment

#### 1. Enable GitHub Actions
- Go to your repository settings
- Navigate to **Actions** → **General**
- Enable "Read and write permissions" for workflows

#### 2. Configure Scraper URLs
Edit `backend/scraper_config.json` to customize which listings to scrape:

```json
{
  "scrapers": [
    {
      "platform": "otomoto",
      "search_url": "https://www.otomoto.pl/osobowe/bmw",
      "pages": 3
    }
  ]
}
```

#### 3. Trigger GitHub Action
- Go to **Actions** tab in your repository
- Select "Car Data Scraper" workflow
- Click "Run workflow"
- Data will be scraped and committed to `frontend/public/data/listings.json`

#### 4. Deploy to GitHub Pages
```bash
cd frontend
npm run build
```

Then configure GitHub Pages to serve from the `frontend/dist` folder, or set up a deployment action.

Alternatively, add this to `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Build
        run: |
          cd frontend
          npm install
          npm run build
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/dist
```

## 📊 Data Schema

Each listing contains:

```json
{
  "source_id": "unique-id",
  "source_url": "https://...",
  "platform": "otomoto|olx|autoplac",
  "brand": "BMW",
  "model": "Seria 3",
  "production_year": 2018,
  "mileage": 150000,
  "price": 45000,
  "currency": "PLN",
  "fuel_type": "Diesel",
  "engine_capacity": 1995,
  "power": 150,
  "body_type": "Sedan",
  "color": "Czarny",
  "condition": "used|new|damaged",
  "location": "Warszawa",
  "created_at_source": "2024-01-15",
  "scraped_at": "2024-01-20T10:30:00"
}
```

## 🛠️ CLI Usage

```bash
# Run all scrapers from config
python cli.py --config scraper_config.json --pages 2

# Scrape specific platform
python cli.py --platform olx --url "URL" --pages 3

# Test mode
python cli.py --test

# Custom output location
python cli.py --config scraper_config.json --output data/custom.json
```

## 📅 Scheduled Scraping

The GitHub Action runs daily at 2 AM UTC. To change the schedule, edit `.github/workflows/scraper.yml`:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

## ⚠️ Important Notes

### Facebook Marketplace & Allegro
These platforms have aggressive bot detection and require:
- Residential proxies
- Browser fingerprinting evasion
- CAPTCHA solving

They are **not included** in this implementation due to GitHub Actions limitations.

### Rate Limiting
Be respectful of the scraped websites:
- Default: 2-3 pages per platform
- 2-second delay between pages
- Runs once per day

### Legal Considerations
- Web scraping may violate Terms of Service
- Use responsibly and only for personal/educational purposes
- Consider using official APIs where available

## 🐛 Troubleshooting

**Scrapers return no data:**
- Website structure may have changed
- Check browser console for errors
- Try running with `headless=False` in scraper code

**GitHub Action fails:**
- Check workflow permissions
- Verify Python dependencies are correct
- Review Action logs for specific errors

**Frontend shows no data:**
- Ensure `frontend/public/data/listings.json` exists
- Check browser console for fetch errors
- Verify file path is correct

## 📝 License

MIT License - Use at your own risk

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Built with**: Python, Playwright, FastAPI, React, Recharts, TailwindCSS
