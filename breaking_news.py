import time
import yaml
import feedparser
import pygame
from threading import Thread
from displays.scrolling_display import ScrollingNewsDisplay


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


def news_monitor(config):
    """
    Monitor RSS feeds and display breaking news
    
    Args:
        config: Configuration dictionary
    """
    display = ScrollingNewsDisplay()
    clock = pygame.time.Clock()
    
    def monitor_feed(feed_config):
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
        if isinstance(feed_config, dict) and 'url' in feed_config:
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
            clock.tick(60)  # 60 FPS
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
