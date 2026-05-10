# brand-consistency-checker

# Brand Consistency Checker

**eslint for brand design** â€” validates AI-generated outputs against your brand rules.

AI tools produce content fast, but nobody checks if it matches your brand. This tool catches off-brand colors, banned words, wrong fonts, and tone violations before they ship.

## Problem

- Designers generate assets with AI, but nobody validates them against brand guidelines
- Marketing copy gets written by LLMs using banned words or wrong tone
- Logos get resized, recolored, or placed on busy backgrounds
- Brand drift happens silently across teams

## Solution

A single CLI/API that takes your brand spec and validates any image or text against it. Run it in CI, in your design pipeline, or as a one-off check.

## Quick Start

```bash
pip install -e .
brand-check init                    # creates brand.yaml template
brand-check check-image \           # validate an image
  --spec brand.yaml \
  --image logo.png
brand-check check-text \            # validate copy
  --spec brand.yaml \
  --text "Check out our insane new product!"
```

## CLI Usage

### `brand-check init`

Generate a `brand.yaml` template to customize with your brand rules.

```bash
brand-check init -o my_brand.yaml
```

### `brand-check check-image`

Validate an image's colors and dimensions against brand rules.

```bash
brand-check check-image --spec brand.yaml --image hero-banner.png
```

Exit code `0` if compliant, `1` if violations found.

### `brand-check check-text`

Check text against voice/tone rules (banned words, sentence length, etc.).

```bash
brand-check check-text --spec brand.yaml --text "Your copy here"
brand-check check-text --spec brand.yaml --file copy.txt
```

### `brand-check report`

Generate a full compliance report across multiple checks.

```bash
brand-check report \
  --spec brand.yaml \
  --image logo.png \
  --text-file ad-copy.txt \
  -o report.txt
```

## API

Run the server:

```bash
uvicorn brand_checker.api:app --reload
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/check/text` | Validate text against brand rules |
| `POST` | `/check/image` | Validate image against brand palette |
| `POST` | `/check/batch` | Run multiple checks at once |
| `POST` | `/spec/validate` | Validate a brand spec file |

### Example: Check text via API

```bash
curl -X POST http://localhost:8000/check/text \
  -F "spec=@brand.yaml" \
  -F "text=Check out our insane new product!"
```

Response:

```json
{
  "passed": false,
  "score": 0.0,
  "checked_items": 2,
  "passed_items": 0,
  "violations": [
    {
      "rule": "voice.banned_word",
      "message": "Banned word found: 'insane'",
      "severity": "error",
      "context": "insane"
    }
  ]
}
```

### Example: Check image via API

```bash
curl -X POST http://localhost:8000/check/image \
  -F "spec=@brand.yaml" \
  -F "image=@logo.png"
```

## Brand Spec Format

The brand spec is a YAML or JSON file with these sections:

### Colors

```yaml
colors:
  - name: "Primary Blue"       # human-readable name
    hex: "#0066CC"             # required: hex color
    pantone: "PMS 2935 C"      # optional
    cmyk: "100, 50, 0, 0"     # optional
```

The checker samples image pixels and flags colors that are far from any palette entry (Euclidean distance in RGB space).

### Typography

```yaml
typography:
  - font_family: "Inter"       # allowed font name
    allowed_sizes: [12, 14, 16, 20, 24, 32]  # optional
    allowed_weights: [400, 600, 700]          # optional
    min_size: 12               # optional
    max_size: 72               # optional
```

### Logo Rules

```yaml
logo:
  min_width_px: 120            # minimum width in pixels
  min_height_px: 40            # minimum height in pixels
  clear_space_ratio: 0.5       # clear space as fraction of logo width
  allowed_formats:             # optional
    - PNG
    - SVG
```

### Voice & Tone

```yaml
voice:
  tone_keywords:               # descriptive (not enforced, for reference)
    - professional
    - friendly
  banned_words:                # words that trigger errors
    - cheap
    - guaranteed
    - revolutionary
  max_sentence_length: 25      # max words per sentence
  max_paragraph_length: 5      # max sentences per paragraph
  required_includes:           # phrases that must appear
    - "Acme Corp"
```

## Running in CI

```yaml
# GitHub Actions example
- name: Check brand consistency
  run: |
    pip install -e .
    brand-check report --spec brand.yaml --text-file "$CONTENT_FILE" -o report.txt
    cat report.txt
```

## License

MIT â€” see [LICENSE](LICENSE).


## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Clone the Repository

```bash
git clone https://github.com/darshd9941/brand-consistency-checker.git
cd brand-consistency-checker
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit .env and add your API keys:
   ```bash
   # Required for Claude vision features
   ANTHROPIC_API_KEY=your-api-key-here
   ```

## Usage

### Web App (if applicable)

```bash
streamlit run app.py
```

### CLI Usage

```bash
python main.py --help
```

### Python API

```python
from module import MainClass

# Initialize the tool
tool = MainClass()

# Use the tool
result = tool.process("input")
print(result)
```

## Configuration

- .env - Environment variables (API keys, settings)
- config.yaml - Configuration file (if applicable)

## Examples

See the examples/ directory for detailed usage examples.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.
