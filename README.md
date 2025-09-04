# 📊 Exa FDA Calendar Scraper

Scrape and structure the [Unusual Whales FDA Calendar](https://unusualwhales.com/fda-calendar) into **JSON** and **CSV** using the [Exa API](https://exa.ai).

---

## ✨ Features

- Fetches page text with **Exa /contents** and **livecrawl** for fresh data  
- Structured extraction via **summary + JSON Schema**  
- Fallback parser for **markdown tables**  
- Exports results to **JSON** and **CSV**  
- Easy to extend with **GitHub Actions** for scheduled updates  

---

## 🛠️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/Jessie-QingYu/exa-fda-calendar-scraper.git
cd exa-fda-calendar-scraper
````

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
# On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` and insert your **Exa API key**:

```
EXA_API_KEY=your_api_key_here
```

You can generate a key in the [Exa Dashboard](https://dashboard.exa.ai).

---

## 🚀 Usage

Run the scraper:

```bash
python -m exa_fda_calendar.cli
```

Customize with options:

```bash
python -m exa_fda_calendar.cli \
  --livecrawl always \
  --min-structured 5 \
  --out-json data/fda_calendar.json \
  --out-csv data/fda_calendar.csv \
  --save-raw
```

Outputs will be saved to `data/`:

* `fda_calendar.json` – structured FDA events
* `fda_calendar.csv` – CSV export of events
* `page_raw.md` – raw extracted page text (debugging only, ignored by Git)

---

## 📂 Project Structure

```
exa-fda-calendar-scraper/
├── src/
│   └── exa_fda_calendar/     # Core scraper package
├── tests/                    # Pytest unit tests
├── data/                     # Output data (JSON/CSV)
│   ├── fda_calendar.json
│   ├── fda_calendar.csv
│   └── page_raw.md
├── .env.example              # Example environment variables
├── .gitignore                # Ignore rules
├── pyproject.toml            # Project metadata
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## ✅ Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit changes (`git commit -m "feat: add new feature"`)
4. Push to branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---






