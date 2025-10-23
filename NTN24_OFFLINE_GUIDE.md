# NTN24 Offline News Guide

Complete guide for downloading and viewing NTN24 news offline.

## Quick Start

### 1. Install Dependencies

```bash
pip install requests beautifulsoup4
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### 2. Download News for Offline Viewing

#### Basic Scraping (headlines only)
```bash
python ntn24_scraper.py
```

#### Full Offline Mode (download everything)
```bash
python ntn24_scraper.py --offline
```

This will download:
- ✓ All HTML pages
- ✓ All CSS stylesheets
- ✓ All JavaScript files
- ✓ All images
- ✓ All fonts

### 3. View Offline Content

After running with `--offline` mode, open in your browser:
```bash
open ntn24_cache/html/index.html
```

Or on Linux:
```bash
xdg-open ntn24_cache/html/index.html
```

## Command Line Options

```bash
# Basic scraping (fast, headlines only)
python ntn24_scraper.py

# Download images too
python ntn24_scraper.py --full-articles

# Complete offline mode (downloads EVERYTHING)
python ntn24_scraper.py --offline

# Custom cache directory
python ntn24_scraper.py --cache-dir ~/Documents/ntn24_archive

# List cached news
python ntn24_scraper.py --list

# Skip images (faster)
python ntn24_scraper.py --no-images
```

## Integration with breaking_news.py

The scraper is integrated into `breaking_news.py`. To enable NTN24:

### 1. Edit config.yaml

```yaml
feeds:
  # NTN24 - Colombian News (scraped from website)
  - name: NTN24
    type: ntn24
    cache_dir: ntn24_cache
    refresh_interval: 600  # 10 minutes

  # Other RSS feeds...
  - name: BBC News
    url: http://feeds.bbci.co.uk/news/world/rss.xml
    refresh_interval: 300
```

### 2. Pre-fetch News (recommended)

Before running `breaking_news.py`, pre-fetch the news:

```bash
# Quick fetch
python ntn24_scraper.py

# Or full offline mode
python ntn24_scraper.py --offline
```

### 3. Run Breaking News Display

```bash
python breaking_news.py
```

NTN24 headlines will automatically appear in the display alongside other news sources.

## Scheduled Updates (Optional)

### macOS with launchd

Create a scheduled task to auto-update news every hour:

```bash
# Create a plist file at ~/Library/LaunchAgents/com.ntn24.scraper.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ntn24.scraper</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/YOUR_USERNAME/GitRepos/BreakingNewsEffects/ntn24_scraper.py</string>
        <string>--offline</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.ntn24.scraper.plist
```

### Linux with cron

```bash
crontab -e
```

Add this line to run every hour:
```
0 * * * * cd /path/to/BreakingNewsEffects && /usr/bin/python3 ntn24_scraper.py --offline
```

## Cache Structure

```
ntn24_cache/
├── html/               # Offline HTML pages
│   ├── index.html     # Homepage
│   └── *.html         # Article pages
├── images/            # Downloaded images
├── css/               # Stylesheets
├── js/                # JavaScript files
├── fonts/             # Web fonts
└── news_*.json        # Cached data (used by breaking_news.py)
```

## Troubleshooting

### "No cache found" error
Run the scraper first:
```bash
python ntn24_scraper.py
```

### Images not showing offline
Use `--offline` mode to download all resources:
```bash
python ntn24_scraper.py --offline
```

### Memory issues with large downloads
Use basic mode without offline:
```bash
python ntn24_scraper.py --no-images
```

### Network errors
The scraper includes retry logic and is rate-limited to be polite. If you see many errors, wait a few minutes and try again.

## Advanced Usage

### Python API

```python
from ntn24_scraper import NTN24Scraper

# Create scraper
scraper = NTN24Scraper(cache_dir='custom_cache')

# Full offline scrape
scraper.scrape_all(offline_mode=True)

# Get news feed for display
feed_items = scraper.get_news_feed()
for item in feed_items:
    print(item['title'])
```

### Integration with Other Projects

```python
from ntn24_scraper import NTN24Scraper

scraper = NTN24Scraper()

# Get latest news
scraper.scrape_all()
news = scraper.get_news_feed()

# Use in your app
for article in news:
    print(f"Title: {article['title']}")
    print(f"Link: {article['link']}")
    print(f"Local Image: {article['image']}")
```

## Notes

- The scraper respects rate limits (0.5-1 second delays)
- Offline mode downloads can take 10-30 minutes for full content
- Cache files are stored locally and persist between runs
- The `doc` folder is excluded from git (as per your rules)

## License

Part of BreakingNewsEffects project.
