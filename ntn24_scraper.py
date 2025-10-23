#!/usr/bin/env python3
"""
NTN24 News Scraper
Prefetches news from https://www.ntn24.com for offline access
"""

import os
import json
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import hashlib
import re
import mimetypes


class NTN24Scraper:
    def __init__(self, cache_dir="ntn24_cache"):
        self.base_url = "https://www.ntn24.com"
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Create cache directory structure
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "articles"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "images"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "css"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "js"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "fonts"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "html"), exist_ok=True)
        
        self.downloaded_urls = set()  # Track downloaded resources
    
    def _get_url_hash(self, url):
        """Generate a hash for URL to use as filename"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def fetch_homepage(self):
        """Fetch the NTN24 homepage"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching homepage: {e}")
            return None
    
    def parse_news_articles(self, html_content):
        """Parse news articles from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = []
        
        # Find all article links (adjust selectors based on actual structure)
        # NTN24 uses image tags with specific patterns
        for img in soup.find_all('img', {'loading': 'lazy'}):
            article_data = {}
            
            # Get image info
            article_data['image_url'] = img.get('src', '')
            article_data['image_alt'] = img.get('alt', '')
            article_data['image_title'] = img.get('title', '')
            
            # Try to find parent link
            parent_link = img.find_parent('a')
            if parent_link:
                article_data['url'] = urljoin(self.base_url, parent_link.get('href', ''))
            
            # Try to find associated text
            parent = img.find_parent(['div', 'article', 'section'])
            if parent:
                text_elem = parent.find(['h2', 'h3', 'p', 'span'])
                if text_elem:
                    article_data['text'] = text_elem.get_text(strip=True)
            
            if article_data.get('image_alt') or article_data.get('text'):
                articles.append(article_data)
        
        return articles
    
    def download_resource(self, resource_url, resource_type="images"):
        """Download and save any resource (image, css, js, font)"""
        if not resource_url or not resource_url.startswith('http'):
            return None
        
        # Skip if already downloaded
        if resource_url in self.downloaded_urls:
            url_hash = self._get_url_hash(resource_url)
            # Return existing path
            for ext in ['.jpg', '.png', '.gif', '.css', '.js', '.woff', '.woff2', '.ttf', '.svg']:
                filepath = os.path.join(self.cache_dir, resource_type, f"{url_hash}{ext}")
                if os.path.exists(filepath):
                    return filepath
        
        try:
            url_hash = self._get_url_hash(resource_url)
            
            # Get extension from URL or content type
            parsed = urlparse(resource_url)
            ext = os.path.splitext(parsed.path)[1]
            
            if not ext:
                # Guess extension from resource type
                ext_map = {
                    'images': '.jpg',
                    'css': '.css',
                    'js': '.js',
                    'fonts': '.woff2'
                }
                ext = ext_map.get(resource_type, '')
            
            filename = f"{url_hash}{ext}"
            filepath = os.path.join(self.cache_dir, resource_type, filename)
            
            # Skip if already exists
            if os.path.exists(filepath):
                self.downloaded_urls.add(resource_url)
                return filepath
            
            response = self.session.get(resource_url, timeout=10)
            response.raise_for_status()
            
            # Write content
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_urls.add(resource_url)
            return filepath
        except Exception as e:
            print(f"Error downloading {resource_type} {resource_url}: {e}")
            return None
    
    def download_image(self, image_url):
        """Download and save image"""
        return self.download_resource(image_url, "images")
    
    def download_page_resources(self, html_content, base_url):
        """Extract and download all resources from HTML (CSS, JS, images, fonts)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Download CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            css_url = link.get('href')
            if css_url:
                full_url = urljoin(base_url, css_url)
                local_path = self.download_resource(full_url, 'css')
                if local_path:
                    # Update link to local path
                    link['href'] = os.path.relpath(local_path, self.cache_dir)
        
        # Download JavaScript files
        for script in soup.find_all('script', src=True):
            js_url = script.get('src')
            if js_url:
                full_url = urljoin(base_url, js_url)
                local_path = self.download_resource(full_url, 'js')
                if local_path:
                    script['src'] = os.path.relpath(local_path, self.cache_dir)
        
        # Download images
        for img in soup.find_all('img', src=True):
            img_url = img.get('src')
            if img_url:
                full_url = urljoin(base_url, img_url)
                local_path = self.download_resource(full_url, 'images')
                if local_path:
                    img['src'] = os.path.relpath(local_path, self.cache_dir)
        
        return str(soup)
    
    def fetch_article(self, article_url, download_resources=False):
        """Fetch full article content"""
        try:
            response = self.session.get(article_url, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract article content
            article_data = {
                'url': article_url,
                'title': '',
                'content': '',
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to find title
            title = soup.find('h1')
            if title:
                article_data['title'] = title.get_text(strip=True)
            
            # Try to find article body
            article_body = soup.find(['article', 'div'], class_=['article-content', 'content', 'post-content'])
            if article_body:
                paragraphs = article_body.find_all('p')
                article_data['content'] = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            
            # Download all resources if requested
            if download_resources:
                modified_html = self.download_page_resources(html_content, article_url)
                
                # Save offline HTML
                url_hash = self._get_url_hash(article_url)
                html_path = os.path.join(self.cache_dir, 'html', f'{url_hash}.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(modified_html)
                article_data['offline_html'] = html_path
            
            return article_data
        except Exception as e:
            print(f"Error fetching article {article_url}: {e}")
            return None
    
    def save_cache(self, data, cache_type="news"):
        """Save scraped data to cache"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{cache_type}_{timestamp}.json"
        filepath = os.path.join(self.cache_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Cache saved: {filepath}")
        return filepath
    
    def load_latest_cache(self, cache_type="news"):
        """Load most recent cache file"""
        pattern = f"{cache_type}_*.json"
        cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith(cache_type) and f.endswith('.json')]
        
        if not cache_files:
            return None
        
        # Get most recent
        latest = sorted(cache_files)[-1]
        filepath = os.path.join(self.cache_dir, latest)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def scrape_all(self, download_images=True, fetch_full_articles=False, offline_mode=False):
        """Main scraping function"""
        print(f"Starting NTN24 scraper at {datetime.now()}")
        print(f"Cache directory: {os.path.abspath(self.cache_dir)}")
        if offline_mode:
            print("OFFLINE MODE: Downloading all resources for complete offline access")
        
        # Fetch homepage
        print("\nFetching homepage...")
        html = self.fetch_homepage()
        if not html:
            print("Failed to fetch homepage")
            return None
        
        # Save homepage for offline access
        if offline_mode:
            modified_html = self.download_page_resources(html, self.base_url)
            homepage_path = os.path.join(self.cache_dir, 'html', 'index.html')
            with open(homepage_path, 'w', encoding='utf-8') as f:
                f.write(modified_html)
            print(f"Saved offline homepage: {homepage_path}")
        
        # Parse articles
        print("\nParsing articles...")
        articles = self.parse_news_articles(html)
        print(f"Found {len(articles)} articles")
        
        # Download images
        if download_images or offline_mode:
            print("\nDownloading images...")
            for i, article in enumerate(articles):
                if article.get('image_url'):
                    print(f"  [{i+1}/{len(articles)}] Downloading image...")
                    local_path = self.download_image(article['image_url'])
                    article['local_image'] = local_path
                    time.sleep(0.5)  # Be polite
        
        # Fetch full articles
        if fetch_full_articles or offline_mode:
            print("\nFetching full articles...")
            for i, article in enumerate(articles):
                if article.get('url'):
                    print(f"  [{i+1}/{len(articles)}] Fetching {article['url'][:50]}...")
                    full_article = self.fetch_article(article['url'], download_resources=offline_mode)
                    if full_article:
                        article['full_content'] = full_article
                    time.sleep(1)  # Be polite
        
        # Save cache
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'source': self.base_url,
            'articles': articles,
            'offline_mode': offline_mode
        }
        
        cache_file = self.save_cache(cache_data)
        print(f"\n✓ Scraping complete! Cached {len(articles)} articles")
        print(f"✓ Cache location: {cache_file}")
        
        if offline_mode:
            print(f"\n✓ OFFLINE MODE: All content downloaded to {os.path.abspath(self.cache_dir)}")
            print(f"✓ Open {os.path.join(self.cache_dir, 'html', 'index.html')} in your browser")
        
        return cache_data
    
    def get_news_feed(self):
        """Get news in a format compatible with breaking_news.py"""
        cache = self.load_latest_cache()
        if not cache:
            print("No cache found. Run scrape_all() first.")
            return []
        
        feed_items = []
        for article in cache.get('articles', []):
            # Create feed-like entries
            title = article.get('image_alt') or article.get('text') or article.get('image_title', 'Sin título')
            
            feed_items.append({
                'title': title,
                'link': article.get('url', ''),
                'id': article.get('url', '') or self._get_url_hash(title),
                'image': article.get('local_image', ''),
                'source': 'NTN24'
            })
        
        return feed_items


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NTN24 News Scraper - Download news for offline viewing')
    parser.add_argument('--cache-dir', default='ntn24_cache', help='Cache directory (default: ntn24_cache)')
    parser.add_argument('--no-images', action='store_true', help='Skip image downloads')
    parser.add_argument('--full-articles', action='store_true', help='Fetch full article content')
    parser.add_argument('--offline', action='store_true', help='OFFLINE MODE: Download ALL content (HTML, CSS, JS, images) for complete offline access')
    parser.add_argument('--list', action='store_true', help='List cached news')
    
    args = parser.parse_args()
    
    scraper = NTN24Scraper(cache_dir=args.cache_dir)
    
    if args.list:
        # List cached news
        feed = scraper.get_news_feed()
        print(f"\n=== Cached News ({len(feed)} articles) ===\n")
        for i, item in enumerate(feed, 1):
            print(f"{i}. {item['title'][:80]}")
            if item.get('link'):
                print(f"   URL: {item['link']}")
            print()
    else:
        # Scrape news
        scraper.scrape_all(
            download_images=not args.no_images,
            fetch_full_articles=args.full_articles,
            offline_mode=args.offline
        )


if __name__ == "__main__":
    main()
