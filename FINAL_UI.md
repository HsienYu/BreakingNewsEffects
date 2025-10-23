# Final UI Configuration

## Clean Scrolling Text Display 📰

The display now shows **only scrolling text** at the bottom:

```
┌─────────────────────────────────────────┐
│                                         │
│         (empty/transparent)             │
│                                         │
│                                         │
│                                         │
└─────────────────────────────────────────┘
  [News scrolling across screen →] ← 25px thin bar
```

## Features ✨

### Scrolling Text at Bottom
- ✅ **Classic news ticker** style
- ✅ **Smooth scrolling** animation
- ✅ **Small font** (28px) - compact and clean
- ✅ **Thin bar** (25px) - minimal space usage
- ✅ **Auto-loops** through all news items
- ✅ **Adaptive speed** - longer headlines scroll slightly slower

### No Title
- ✅ No "BREAKING NEWS" text
- ✅ Clean, minimal design
- ✅ Maximum screen space for your content

## Perfect For:

- 🎥 **OBS overlays** (with green screen or transparent mode)
- 📺 **Background displays** (monitors, digital signage)
- 🎮 **Streaming** (news ticker for streams)
- 📹 **Video production** (lower third news ticker)

## Usage

### Run the display:
```bash
python3 breaking_news.py
```

### Test with sample data:
```bash
python3 test_hybrid_ui.py
```

### Download NTN24 news first:
```bash
python3 ntn24_scraper.py
```

## Configuration

### In `config.yaml`:

```yaml
# Display Settings
transparent_background: false  # Set to true for transparent overlay
green_screen: true            # Set to true for chroma key in OBS

feeds:
  - name: NTN24
    type: ntn24
    cache_dir: ntn24_cache
    refresh_interval: 600

  - name: BBC News
    url: http://feeds.bbci.co.uk/news/world/rss.xml
    refresh_interval: 300
```

## Controls

| Key | Action |
|-----|--------|
| ESC | Exit the display |

No scrolling controls needed - it's automatic! 🎯

## Visual Modes

### 1. Transparent Mode (for OBS overlay)
```yaml
transparent_background: true
green_screen: false
```
- Main area is fully transparent
- Only the thin red bar with scrolling text is visible
- Perfect for overlaying on other content

### 2. Green Screen Mode (for chroma key)
```yaml
transparent_background: false
green_screen: true
```
- Main area is bright green (0, 255, 0)
- Use OBS Chroma Key filter to remove green
- Works with any video software that supports chroma keying

### 3. Solid Background Mode
```yaml
transparent_background: false
green_screen: false
```
- Main area is solid black
- Red bar at bottom with scrolling text
- Standalone display mode

## Technical Details

### Bottom Bar Specs:
- **Height:** 25px (thin)
- **Color:** Semi-transparent red (200, 0, 0, 220)
- **Font size:** 28px
- **Scroll speed:** 2.5 pixels per frame (adaptive for long text)

### Performance:
- **60 FPS** smooth scrolling
- **Text caching** for efficiency
- **Low CPU usage** (~5-10% on modern systems)
- **Adaptive speed** prevents blur on long headlines

### Streaming Output:
Priority order:
1. **Spout** (Windows - best for OBS)
2. **NDI** (Cross-platform)
3. **Syphon** (macOS)
4. **HTTP/UDP** (Fallback)

## Example Workflow

### For OBS Overlay:

1. **Set config to green screen mode:**
   ```yaml
   green_screen: true
   ```

2. **Run the display:**
   ```bash
   python3 breaking_news.py
   ```

3. **In OBS:**
   - Add Spout2 Capture source (Windows)
   - Or add Window Capture → Select "Breaking News"
   - Add Filter → Chroma Key
   - Set Key Color Type to "Green"
   - Adjust Similarity/Smoothness as needed

4. **Result:** 
   Clean scrolling news ticker at bottom of your stream! 🎬

## Tips

1. **Resize window** to fit your layout
2. **Use with multiple feeds** for continuous news
3. **Pre-cache NTN24** for offline operation
4. **Adjust refresh intervals** to control update frequency
5. **Use green screen mode** for easiest OBS integration

## File Structure

```
BreakingNewsEffects/
├── breaking_news.py          ← Main app
├── ntn24_scraper.py          ← NTN24 news scraper
├── config.yaml               ← Configuration
├── displays/
│   └── scrolling_display.py ← UI (modified)
└── ntn24_cache/             ← Cached news
    ├── html/                ← Offline HTML
    ├── images/              ← Downloaded images
    └── news_*.json          ← News data
```

## What Changed

From the original design:
- ❌ Removed "BREAKING NEWS" title at top
- ❌ Removed scrollable news list
- ✅ Kept scrolling text at bottom
- ✅ Made bottom bar thinner (40px → 25px)
- ✅ Made font smaller (48px → 28px)
- ✅ Cleaner, more minimal look

Perfect for overlays and minimal displays! 🎉
