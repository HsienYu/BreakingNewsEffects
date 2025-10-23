# Hybrid UI: Scrollable List + Scrolling Text

## New Design ✨

The display now combines **both** viewing modes:

```
┌─────────────────────────────────────────┐
│  • News item 3 (mixed order)            │ ← Scrollable list
│  • News item 1                           │    (scroll with mouse/keys)
│  • News item 5                           │
│  • News item 2                           │
│  • News item 4                           │
│    ↕ (scroll to see more)                │
│                                          │
└──────────────────────────────────────────┘
  [News scrolling across screen →] ← 25px bar
```

## Features

### 1. **Scrollable List (Main Area)** 📜
- Shows all news items with bullet points
- **Mixed/Random Order** - News appears in random positions
- Scroll with:
  - **Mouse wheel** ↕
  - **Up/Down arrow keys** ⬆️⬇️

### 2. **Scrolling Text (Bottom Bar)** 📰
- Classic scrolling ticker at the bottom
- Automatically cycles through all news
- Smooth horizontal scrolling animation
- Adaptive speed based on text length

### 3. **Mixed Order** 🔀
- Each new headline is inserted at a **random position** in the list
- Keeps the display dynamic and unpredictable
- Prevents news from appearing in chronological order

## Visual Layout

### Full Screen View:
```
┌──────────────────────────────────────────────────┐
│                                                  │
│  • Reuters: Global markets surge                │ ← List Area
│  • NTN24: Breaking political news                │   (scrollable)
│  • BBC: Weather update                           │
│  • CNN: Sports headlines                         │
│  • Al Jazeera: International affairs             │
│  • Reuters: Economic report                      │
│                                                  │
│    (scroll for more news...)                     │
│                                                  │
└──────────────────────────────────────────────────┘
  [  BBC: Weather update scrolling... →  ] ← Bottom bar (auto-scrolling)
```

## How It Works

1. **News arrives** from feeds (RSS, NTN24, etc.)
2. **Added to list** at a random position (mixed order)
3. **Also added to scrolling queue** for bottom ticker
4. **List is scrollable** - view all items at your own pace
5. **Bottom scrolls automatically** - classic news ticker style

## Controls

| Action | Method |
|--------|--------|
| Scroll list up | Mouse wheel up OR Up arrow key |
| Scroll list down | Mouse wheel down OR Down arrow key |
| Exit | ESC key |
| Resize window | Drag window edges |

## Advantages

### Best of Both Worlds:
- ✅ **List view** - See multiple headlines at once
- ✅ **Scrolling text** - Classic TV news ticker feel
- ✅ **Mixed order** - Dynamic, non-chronological display
- ✅ **User control** - Scroll at your own pace
- ✅ **Auto-play** - Bottom ticker runs automatically

### Use Cases:
- **Background display** - Let it scroll automatically
- **Active reading** - Scroll through the list manually
- **Multi-tasking** - Glance at scrolling text, dive into list when needed

## Technical Details

### Data Flow:
```
New headline arrives
     ↓
Split into two streams:
     ↓                    ↓
List (random insert)   Scrolling Queue
     ↓                    ↓
User scrollable       Auto-scrolling
     ↓                    ↓
Main display area    Bottom bar
```

### Cache Keys:
- List items: `list_{news_text}`
- Scrolling items: `scroll_{news_text}`
- Separate caching for optimal performance

### Performance:
- Only visible list items are rendered
- Text surfaces are cached
- Smooth 60 FPS scrolling
- Efficient memory usage

## Configuration

### In `config.yaml`:
```yaml
feeds:
  - name: NTN24
    type: ntn24
    cache_dir: ntn24_cache
    refresh_interval: 600
  
  - name: BBC News
    url: http://feeds.bbci.co.uk/news/world/rss.xml
    refresh_interval: 300
```

### Display Settings:
```python
# In breaking_news.py, these are set via config.yaml:
transparent_background: false
green_screen: true  # or false
```

## Examples

### Mixed Order in Action:

News arrives in this order:
1. "First headline"
2. "Second headline"  
3. "Third headline"

List displays (random):
- • Third headline
- • First headline
- • Second headline

Bottom scrolls (in arrival order):
- "First headline" → "Second headline" → "Third headline" → (loop)

## Future Enhancements

Possible additions:
- **Color coding** by source (BBC=blue, NTN24=red, etc.)
- **Timestamps** on each item
- **Priority markers** for breaking news
- **Grouping** by category
- **Search/filter** in list
- **Click to expand** full article
- **Export** list to file

## Tips

1. **Let it run** - Perfect for background monitoring
2. **Scroll when needed** - Catch up on missed headlines
3. **Resize as needed** - Works at any window size
4. **Mix feeds** - Combine RSS and scraped sources
5. **Green screen mode** - For OBS overlay (chroma key)

Enjoy your hybrid news display! 📺✨
