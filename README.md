# Drink Pace Guide

Drink Pace Guide is a responsive Flask web application that provides an educational estimate of how a combination of drinks, elapsed drinking time, and food timing may affect blood alcohol concentration (BAC). It is not medical advice, a measurement of BAC, or a guarantee of how someone will feel.

## Features

- Live mixed-drink calculator backed by a Flask JSON API
- Simplified Widmark BAC estimate with food-and-timing peak adjustment
- BAC uncertainty range, category, colour meter, and drink summary
- Educational mixed-drink combination explorer
- Client-side and server-side validation
- Responsive interface and a collapsible sources and limitations section

## Installation

Install Python 3.9 or newer, then open this project folder in VS Code.

Create and activate a virtual environment:

```powershell
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies and run the app:

```powershell
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080) in a browser. Stop the server with `Ctrl+C`.

## Calculation

The application treats one U.S. standard drink as approximately 14 grams of pure alcohol. The backend calculates:

```text
alcohol_grams = total_standard_drinks * 14
r = 0.68 for male, 0.55 for female
initial_bac = (alcohol_grams / (weight_kg * 1000 * r)) * 100
unadjusted_bac = max(0, initial_bac - (0.015 * drinking_hours))
food_adjusted_peak = unadjusted_bac * (1 - food_reduction)
```

Food adjustment is a simplified educational estimate based on meal size and the time between the meal and first drink; it is not a clinically validated fixed BAC correction. A randomized trial of specific meals found approximately 30% lower alcohol exposure over time compared with fasting, but individual results and peak BAC effects vary. The app pairs its estimate with a plus/minus 20% uncertainty range. Height and age are recorded for context but are not used for a pretend-precise adjustment.

## Limitations and safety

This calculator is an educational model only. Cocktail recipes and pours vary, food can delay absorption but does not remove alcohol, and BAC estimates cannot predict behaviour or subjective feelings. People can be impaired before they feel drunk.

Never use this estimate to decide whether it is safe to drive or perform other risky activities. The only reliable way to know BAC is appropriate testing. If someone is difficult to wake, vomiting repeatedly, breathing slowly or irregularly, confused, having seizures, or has pale/blue skin, contact emergency services immediately and do not leave them alone.

Sources are linked in the app: NIAAA standard drink guidance, CDC standard drink sizes, NIAAA alcohol drinking patterns, NIAAA food and absorption information, NIAAA hangover information, a PubMed reference on the Widmark equation, and a PubMed randomized trial on food and alcohol absorption: Staudt et al., "Optimized food: A strategy for reducing blood alcohol concentration" (2026), https://pubmed.ncbi.nlm.nih.gov/42524898/.
