# BreakingNewsEffects

A real-time RSS news ticker application that displays breaking news as scrolling text, with optional Syphon output for macOS systems.

## Features

- **Real-time RSS Monitoring**: Automatically fetches news from multiple RSS feeds
- **Scrolling News Ticker**: Displays breaking news in a scrolling text format
- **Syphon Integration**: Sends the video output to other applications on macOS via Syphon
- **Configurable Feed Sources**: Easily configure multiple news sources via YAML
- **Customizable Refresh Rates**: Set different refresh intervals for each news source

## Requirements

- Python 3.6+
- pygame 2.5.0+
- PyYAML 6.0+
- feedparser 6.0.0+
- numpy 1.20.0+
- PyOpenGL 3.1.0+ (for OpenGL-based Syphon support)
- syphon-python 0.1.0+ (for macOS Syphon support)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/BreakingNewsEffects.git
   cd BreakingNewsEffects
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. For macOS users who want Syphon support:
   ```
   pip install syphon-python
   ```

## Configuration

Edit the `config.yaml` file to set up your RSS feeds:

```yaml
feeds:
  - name: BBC News
    url: http://feeds.bbci.co.uk/news/world/rss.xml
    refresh_interval: 120  # in seconds
  
  - name: Reuters
    url: https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best
    refresh_interval: 180
```

## Usage

To start the application:

```
python breaking_news.py
```

The news ticker will appear in a window, displaying breaking news headlines as they are fetched from the configured RSS feeds.

### Syphon Output (macOS only)

If you're on macOS and have the syphon-python package installed, the application will automatically create a Syphon server named "Breaking News" that you can use to receive the video output in applications like OBS, VDMX, Resolume, etc.

## Display Customization

You can modify the appearance of the ticker by editing the parameters in the `ScrollingNewsDisplay` initialization:

- Window size
- Background color
- Text color
- Font and size
- Scroll speed

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).

This means you are free to:
- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following terms:
- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- NonCommercial — You may not use the material for commercial purposes.
- ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

For more details: https://creativecommons.org/licenses/by-nc-sa/4.0/

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
