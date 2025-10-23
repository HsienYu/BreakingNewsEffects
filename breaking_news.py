import time
import yaml
import feedparser
import pygame
from threading import Thread
from displays.scrolling_display import ScrollingNewsDisplay
try:
    from ntn24_scraper import NTN24Scraper
    NTN24_AVAILABLE = True
except ImportError:
    NTN24_AVAILABLE = False
    print("Warning: ntn24_scraper not available. Install dependencies: pip install requests beautifulsoup4")


def load_config(path="config.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def fetch_feed(url, refresh_interval=300):
    """
    Fetch news from an RSS feed
    
    Args:
        url: URL of the RSS feed
        refresh_interval: Time in seconds between feed refreshes
        
    Returns:
        Generator yielding new entries as they appear
    """
    known_entries = set()
    
    while True:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Use entry id or link as unique identifier
                entry_id = entry.get('id', entry.get('link', ''))
                if entry_id and entry_id not in known_entries:
                    known_entries.add(entry_id)
                    yield entry
        except Exception as e:
            print(f"Error fetching feed: {e}")
        
        time.sleep(refresh_interval)


def fetch_ntn24(cache_dir="ntn24_cache", refresh_interval=300):
    """
    Fetch news from NTN24 using the scraper
    
    Args:
        cache_dir: Directory to store cached news
        refresh_interval: Time in seconds between scrapes
        
    Returns:
        Generator yielding new entries as they appear
    """
    if not NTN24_AVAILABLE:
        print("NTN24 scraper not available. Skipping.")
        return
    
    scraper = NTN24Scraper(cache_dir=cache_dir)
    known_entries = set()
    
    while True:
        try:
            # Scrape NTN24
            print("Refreshing NTN24 news...")
            scraper.scrape_all(download_images=False, fetch_full_articles=False)
            
            # Get feed items
            feed_items = scraper.get_news_feed()
            
            for item in feed_items:
                entry_id = item.get('id', item.get('link', ''))
                if entry_id and entry_id not in known_entries:
                    known_entries.add(entry_id)
                    # Convert to feedparser-like format
                    entry = {
                        'title': item['title'],
                        'link': item.get('link', ''),
                        'id': entry_id
                    }
                    yield entry
        except Exception as e:
            print(f"Error fetching NTN24: {e}")
        
        time.sleep(refresh_interval)


def news_monitor(config):
    """
    Monitor RSS feeds and display breaking news
    
    Args:
        config: Configuration dictionary
    """
    # Get NDI configuration from config, if available
    ndi_config = config.get('ndi', {})
    transparent_bg = config.get('transparent_background', True)
    green_screen = config.get('green_screen', False)
    display = ScrollingNewsDisplay(ndi_config=ndi_config, transparent_bg=transparent_bg, green_screen=green_screen)
    clock = pygame.time.Clock()
    
    def monitor_feed(feed_config):
        # Check if this is an NTN24 feed
        if feed_config.get('type') == 'ntn24':
            cache_dir = feed_config.get('cache_dir', 'ntn24_cache')
            refresh_interval = feed_config.get('refresh_interval', 300)
            
            for entry in fetch_ntn24(cache_dir, refresh_interval):
                if not display.is_running():
                    break
                    
                title = entry.get('title', 'No title')
                source = feed_config.get('name', 'NTN24')
                display.show_news(f"{source.upper()}: {title}")
                print(f"New headline: {source.upper()}: {title}")
        else:
            # Standard RSS feed
            feed_url = feed_config['url']
            refresh_interval = feed_config.get('refresh_interval', 300)
            
            for entry in fetch_feed(feed_url, refresh_interval):
                if not display.is_running():
                    break
                    
                title = entry.get('title', 'No title')
                source = feed_config.get('name', 'News')
                # Format the text with source highlighted
                display.show_news(f"{source.upper()}: {title}")
                # Log to console for debugging
                print(f"New headline: {source.upper()}: {title}")
    
    # Start a thread for each feed
    threads = []
    for feed_config in config.get('feeds', []):
        # Make sure feed_config is a dictionary
        # For NTN24 feeds, 'url' is not required (uses scraper instead)
        is_valid = isinstance(feed_config, dict) and (
            'url' in feed_config or feed_config.get('type') == 'ntn24'
        )
        
        if is_valid:
            thread = Thread(target=monitor_feed, args=(feed_config,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            print(f"Started monitoring feed: {feed_config.get('name', 'Unnamed feed')}")
        else:
            print(f"Invalid feed configuration: {feed_config}")
    
    if not threads:
        print("No valid feeds configured. Please check your config.yaml file.")
        display.show_news("NO FEEDS CONFIGURED • Please check config.yaml")
    
    # Main loop - keep updating the display in the main thread
    try:
        while display.is_running() and threads:
            display.update()
            clock.tick(display.target_fps)  # Use the display's target FPS (30 FPS for lower CPU usage)
    except KeyboardInterrupt:
        print("Shutting down news monitor")
    finally:
        # Make sure to clean up pygame
        display.close()


def main():
    config = load_config()
    news_monitor(config)


if __name__ == "__main__":
    main()
