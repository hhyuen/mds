"""
create_pdf.py

Builds a single captioned PDF from screenshots in the screenshots/ folder.
Order and captions are hardcoded below since filenames don't change.

Fix vs previous version: each page is now sized to match the image's
native pixel resolution (plus a caption header strip), instead of forcing
every screenshot into a fixed A4 box. This avoids downscaling that made
chart text/data points unreadable.

Edit ORDERED_IMAGES to control:
  - which images are included
  - what order they appear in the PDF
  - what caption is printed above each image
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader
from PIL import Image

SCREENSHOTS_DIR = Path("screenshots")
OUTPUT_PDF = SCREENSHOTS_DIR / "screenshots.pdf"

# --- EDIT THIS LIST: (filename, caption) in the exact order you want them in the PDF ---
ORDERED_IMAGES = [
    ("finviz.png", "1. Market Performance — intraday key indices performance in previous trading session (S&P 500, NASDAQ, DOW, RUSSELL 2000)"),
    ("heatmap_d.png", "1. Market Performance — sectors and industries heatmap based on daily change data"),
    ("heatmap_w.png", "1. Market Performance — sectors and industries heatmap based on weekly change data"),
    ("fear-greed.png", "2. Market Sentiment — Fear & Greed Index (Excessive fear tends to drive down share prices, and too much greed tends to have the opposite effect)"),
    ("naaim.png", "2. Market Sentiment — NAAIM Exposure Index (Actual adjustments active risk managers have made to client accounts over the past two weeks)"),
    ("aaii.png", "2. Market Sentiment — AAII Investor Sentiment Survey (Opinions of individual investors on where the market is heading in the next six months)"),
    ("ushl.png", "3. Market Breadth — $USHL (Positive net new highs show broad market strength and a healthy bull market) & $NYAD (A rising NYAD confirms that a market rally is backed by widespread stock participation) and their respective 10-Day Moving Average"),
    ("abv50200_SP500.png", "3. Market Breadth — S&P500 Percent of Stocks Above 50 Day & 200 Day Moving Average and their respective 10-Day Moving Average"),
    ("abv50200_COMPQ.png", "3. Market Breadth — COMPQ Percent of Stocks Above 50 Day & 200 Day Moving Average and their respective 10-Day Moving Average"),
    ("abv50200_NYA.png", "3. Market Breadth — NYSE Percent of Stocks Above 50 Day & 200 Day Moving Average and their respective 10-Day Moving Average"),
    ("abv50200_INDU.png", "3. Market Breadth — Dow Jones Industrials Percent of Stocks Above 50 Day & 200 Day Moving Average and their respective 10-Day Moving Average"),
    ("vix.png", "4. Exit Indicator — $VIX (Values below 20 indicate a calm market, while values above 30 signal high investor anxiety, uncertainty, or market sell-offs)"),
    ("hyioas.png", "4. Exit Indicator — US High Yield Index Option-Adjusted Spread (Value below 4 signals a strong economy where investors are confident and willing to accept less premium for taking on default risk, while value above 5 signals extreme market stress, economic fear, or an impending recession as investors panic-sell corporate debt)"),
    ("cme.png", "5. Economic Indicator — Conidtional Meeting Probabilities (Likelihood that the Fed will change the Federal target rate at upcoming FOMC meetings)"),
    ("t10y3m.png", "5. Economic Indicator — 10-Year Treasury Constant Maturity Minus 30Month Treasury Constant Maturity (Positve means investors expect the economy to grow and demand higher interest rates against inflation; Negative means extreme investor anxiety, investors believe economic trouble is brewing soon and rush to lock in long-term 10-year yields before the Federal Reserve is forced to slash interest rates to combat a recession)"),
    ("yieldcurve.png", "5. Economic Indicator — Normally slopes up from left to right, implies healthy, expanding economy with normal inflation expecations; Flat implies economic transition or uncertainty; Inverted implies heavy fear of an impending recession"),
    ("earnings-calendar.png", "6. Imortant Events — Earnings Calendar (For upcoming big names)"),
    ("spotgamma-earnings.png", "6. Implied Earnings Moves Chart for Top Names — The estimated move is based off of the at-the-money straddle for the first expiration date after a stock’s scheduled earnings date"),
    ("economic-calendar.png", "6. Imortant Events — Economic Calendar (For upcoming major US events)")
    # Add more (filename, caption) pairs here as needed
]
# ------------------------------------------------------------------------------------------

# Points-per-pixel at 1:1 (72 pt/inch, assume image pixels map directly to points
# so resolution is preserved exactly — no scaling up or down).
PPI_SCALE = 1.0

MARGIN_LEFT = 20
MARGIN_RIGHT = 20
MARGIN_TOP = 20
MARGIN_BOTTOM = 20
CAPTION_FONT = "Helvetica-Bold"
CAPTION_SIZE = 14
CAPTION_LINE_HEIGHT = 18
CAPTION_GAP_BELOW = 10


def wrap_text(text, font_name, font_size, max_width):
    """Break text into lines that each fit within max_width."""
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    return lines or [text]


def build_pdf():
    files = []
    missing = []
    for filename, caption in ORDERED_IMAGES:
        path = SCREENSHOTS_DIR / filename
        if path.exists():
            files.append((path, caption))
        else:
            missing.append(filename)

    if missing:
        print(f"Warning: missing files skipped: {missing}")

    if not files:
        raise SystemExit("No matching PNG files found in screenshots/. Check ORDERED_IMAGES.")

    c = None

    for path, caption in files:
        img = Image.open(path)
        iw, ih = img.size

        draw_w = iw * PPI_SCALE
        draw_h = ih * PPI_SCALE

        content_width = draw_w
        max_caption_width = content_width  # captions wrap to the image width

        caption_lines = wrap_text(caption, CAPTION_FONT, CAPTION_SIZE, max_caption_width)
        caption_block_height = len(caption_lines) * CAPTION_LINE_HEIGHT

        page_w = MARGIN_LEFT + content_width + MARGIN_RIGHT
        page_h = MARGIN_TOP + caption_block_height + CAPTION_GAP_BELOW + draw_h + MARGIN_BOTTOM

        if c is None:
            c = canvas.Canvas(str(OUTPUT_PDF), pagesize=(page_w, page_h))
        else:
            c.setPageSize((page_w, page_h))

        c.setFont(CAPTION_FONT, CAPTION_SIZE)
        text_y = page_h - MARGIN_TOP - CAPTION_SIZE
        for line in caption_lines:
            c.drawString(MARGIN_LEFT, text_y, line)
            text_y -= CAPTION_LINE_HEIGHT

        image_y = MARGIN_BOTTOM
        c.drawImage(
            ImageReader(img),
            MARGIN_LEFT, image_y,
            width=draw_w, height=draw_h,
            preserveAspectRatio=False, mask='auto'
        )
        c.showPage()

    c.save()
    print(f"Created {OUTPUT_PDF} with {len(files)} page(s) at native resolution.")


if __name__ == "__main__":
    build_pdf()
