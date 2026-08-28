const form = document.querySelector('#calculator-form');
const errorBox = document.querySelector('#form-error');
const targetBand = document.querySelector('[name="target_band"]');
let debounceTimer;

const formatBac = (value) => `${Number(value).toFixed(3)}%`;
const categoryEmoji = {
  'Low alcohol level': '🟢',
  Tipsy: '🟠',
  Drunk: '🔴',
  'Very high alcohol level': '🚨',
};

function payload() {
  const values = new FormData(form);
  return {
    gender: values.get('gender'),
    weight: values.get('weight'),
    duration: values.get('duration'),
    meal_size: values.get('meal_size'),
    meal_timing: values.get('meal_timing'),
    cocktail_type: values.get('cocktail_type'),
    target_band: targetBand.value,
    drinks: Object.fromEntries(['beer', 'vodka_gin', 'tequila', 'whisky', 'wine', 'cocktails'].map((name) => [name, values.get(name)])),
  };
}

function setText(id, text) {
  document.querySelector(id).textContent = text;
}

function renderCombinations(items) {
  const list = document.querySelector('#combination-list');
  list.replaceChildren();
  if (!items.length) {
    const message = document.createElement('p');
    message.textContent = 'No examples are shown for this range because the estimate would be dangerously high.';
    list.append(message);
    return;
  }
  for (const item of items) {
    const entry = document.createElement('article');
    const title = document.createElement('strong');
    const details = document.createElement('span');
    title.textContent = item.summary;
    details.textContent = `${item.total_standard_drinks} standard drinks · estimated BAC range ${formatBac(item.bac_low)}–${formatBac(item.bac_high)}`;
    entry.append(title, details);
    list.append(entry);
  }
}

function render(result) {
  setText('#total-drinks', result.total_standard_drinks);
  setText('#bac-range', `${formatBac(result.bac_low)}–${formatBac(result.bac_high)}`);
  const category = document.querySelector('#category');
  category.textContent = `${categoryEmoji[result.category]} ${result.category}`;
  category.className = result.category.includes('Low') ? 'lower' : result.category.includes('high') || result.category === 'Drunk' ? 'danger' : 'caution';
  setText('#category-note', result.category === 'Drunk' ? 'Please take care.' : '');
  setText('#food-effect', `Food may lower the estimated peak by up to ${result.food_reduction_percent}%. It does not remove alcohol.`);
  setText('#drink-summary', `Your drinks: ${result.drink_summary}.`);
  setText('#combination-food-effect', `Meal adjustment included: up to ${result.food_reduction_percent}% lower estimated peak.`);
  document.querySelector('#high-warning').hidden = targetBand.value !== 'high';
  renderCombinations(result.combinations);
}

async function calculate() {
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  errorBox.hidden = true;
  try {
    const response = await fetch('/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload()),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The estimate could not be calculated.');
    render(result);
  } catch (error) {
    errorBox.textContent = error.message || 'A server error occurred. Please try again.';
    errorBox.hidden = false;
  }
}

function scheduleCalculation() {
  window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(calculate, 250);
}

form.addEventListener('input', scheduleCalculation);
form.addEventListener('change', scheduleCalculation);
targetBand.addEventListener('change', scheduleCalculation);
form.addEventListener('submit', (event) => { event.preventDefault(); window.clearTimeout(debounceTimer); calculate(); });
form.addEventListener('reset', () => { window.setTimeout(calculate, 0); });
calculate();
