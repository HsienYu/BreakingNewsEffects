# Quick Start: NTN24 Offline News

## 🚀 Setup (One-time)

```bash
# Run the setup script
./setup_ntn24.sh
```

Or manually:
```bash
pip3 install requests beautifulsoup4
```

## 📥 Download News for Offline Viewing

### Option 1: Quick Headlines (Recommended for testing)
```bash
python3 ntn24_scraper.py
```
⏱️ Takes ~30 seconds

### Option 2: Complete Offline Mode
```bash
python3 ntn24_scraper.py --offline
```
⏱️ Takes 10-30 minutes (downloads HTML, CSS, JS, images, fonts)

## 👀 View Offline News

### In Browser (if you used --offline mode)
```bash
open ntn24_cache/html/index.html
```

### In Breaking News Display
```bash
python3 breaking_news.py
```

## 📋 List Cached Headlines
```bash
python3 ntn24_scraper.py --list
```

## 🔄 Update News
Just run the scraper again:
```bash
python3 ntn24_scraper.py --offline
```

## 📂 Cache Location
All downloaded content is stored in: `ntn24_cache/`

```
ntn24_cache/
├── html/          ← Open index.html in browser
├── images/        ← Downloaded images
├── css/           ← Stylesheets
├── js/            ← JavaScript
└── news_*.json    ← Data for breaking_news.py
```

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
feeds:
  - name: NTN24
    type: ntn24
    cache_dir: ntn24_cache
    refresh_interval: 600  # Update every 10 minutes
```

## 💡 Tips

1. **First time**: Run `python3 ntn24_scraper.py` before starting `breaking_news.py`
2. **Automatic updates**: Set up cron (Linux) or launchd (macOS) - see NTN24_OFFLINE_GUIDE.md
3. **Save bandwidth**: Use `--no-images` flag for text-only
4. **Full offline**: Use `--offline` once, then view locally anytime

## 📚 More Info

See `NTN24_OFFLINE_GUIDE.md` for:
- Scheduled updates
- Advanced usage
- Troubleshooting
- Python API reference

## ⚙️ How It Works

1. **Scraper** downloads NTN24 homepage and articles
2. **Cache** stores everything locally (JSON + HTML)
3. **breaking_news.py** reads from cache and displays headlines
4. **Offline HTML** can be viewed in any browser

No internet needed after initial download! 🎉
