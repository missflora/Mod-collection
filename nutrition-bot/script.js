// Profile: 64 kg → 58 kg, ~1400 kcal/day (500 kcal deficit from ~1900 TDEE)
const DAILY_GOAL = 1400;

// Quick-add presets: shakes/meal replacements + common healthy Chinese dishes
const PRESETS = [
  { name: "Protein Shake",      cal: 150, protein: 25, carbs: 8,  fat: 3  },
  { name: "Meal Replace. Shake",cal: 200, protein: 20, carbs: 24, fat: 5  },
  { name: "Steamed Egg",        cal: 80,  protein: 8,  carbs: 1,  fat: 5  },
  { name: "Congee (plain)",     cal: 120, protein: 3,  carbs: 25, fat: 1  },
  { name: "Steamed Fish",       cal: 150, protein: 28, carbs: 0,  fat: 4  },
  { name: "Stir-fry Veg",       cal: 90,  protein: 3,  carbs: 10, fat: 4  },
  { name: "Tofu Soup",          cal: 100, protein: 10, carbs: 4,  fat: 5  },
  { name: "Brown Rice (½ cup)", cal: 110, protein: 3,  carbs: 23, fat: 1  },
  { name: "Boiled Chicken",     cal: 165, protein: 31, carbs: 0,  fat: 4  },
  { name: "Wonton Soup",        cal: 180, protein: 12, carbs: 20, fat: 5  },
  { name: "Green Tea (cup)",    cal: 0,   protein: 0,  carbs: 0,  fat: 0  },
];

const STORAGE_KEY = "calorie-log";
const DATE_KEY    = "calorie-date";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function loadLog() {
  const saved = localStorage.getItem(STORAGE_KEY);
  const date  = localStorage.getItem(DATE_KEY);
  if (date !== todayStr()) {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.setItem(DATE_KEY, todayStr());
    return [];
  }
  return saved ? JSON.parse(saved) : [];
}

function saveLog(log) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(log));
  localStorage.setItem(DATE_KEY, todayStr());
}

let log = loadLog();

function addEntry(entry) {
  entry.id = Date.now();
  log.push(entry);
  saveLog(log);
  render();
}

function removeEntry(id) {
  log = log.filter(e => e.id !== id);
  saveLog(log);
  render();
}

function addCustomEntry() {
  const name    = document.getElementById("food-name").value.trim();
  const cal     = parseFloat(document.getElementById("food-cal").value)     || 0;
  const protein = parseFloat(document.getElementById("food-protein").value) || 0;
  const carbs   = parseFloat(document.getElementById("food-carbs").value)   || 0;
  const fat     = parseFloat(document.getElementById("food-fat").value)     || 0;

  if (!name || cal <= 0) {
    alert("Please enter a food name and calories.");
    return;
  }

  addEntry({ name, cal, protein, carbs, fat });

  ["food-name","food-cal","food-protein","food-carbs","food-fat"]
    .forEach(id => { document.getElementById(id).value = ""; });
}

function resetDay() {
  if (!confirm("Reset today's log?")) return;
  log = [];
  saveLog(log);
  render();
}

function render() {
  const totals = log.reduce(
    (acc, e) => ({
      cal:     acc.cal     + e.cal,
      protein: acc.protein + e.protein,
      carbs:   acc.carbs   + e.carbs,
      fat:     acc.fat     + e.fat,
    }),
    { cal: 0, protein: 0, carbs: 0, fat: 0 }
  );

  const remaining = DAILY_GOAL - totals.cal;
  const pct = Math.min((totals.cal / DAILY_GOAL) * 100, 100);
  const over = totals.cal > DAILY_GOAL;

  document.getElementById("consumed").textContent = totals.cal.toFixed(0);

  const remEl = document.getElementById("remaining");
  remEl.textContent = over
    ? `${Math.abs(remaining).toFixed(0)} over`
    : `${remaining.toFixed(0)} left`;
  remEl.className = "cal-remaining " + (over ? "over" : "ok");

  const fill = document.getElementById("progress-fill");
  fill.style.width = pct + "%";
  fill.className = "progress-bar-fill" + (over ? " over" : "");

  document.getElementById("m-protein").textContent = totals.protein.toFixed(0) + "g";
  document.getElementById("m-carbs").textContent   = totals.carbs.toFixed(0)   + "g";
  document.getElementById("m-fat").textContent     = totals.fat.toFixed(0)     + "g";

  // Log list
  const list = document.getElementById("log-list");
  if (log.length === 0) {
    list.innerHTML = '<li class="empty-log">No entries yet — add your first meal!</li>';
    return;
  }

  list.innerHTML = log.slice().reverse().map(e => `
    <li class="log-item">
      <div>
        <div class="log-name">${escHtml(e.name)}</div>
        <div class="log-meta">P ${e.protein}g &nbsp;C ${e.carbs}g &nbsp;F ${e.fat}g</div>
      </div>
      <div style="display:flex;align-items:center">
        <span class="log-cal">${e.cal} kcal</span>
        <button class="log-del" onclick="removeEntry(${e.id})" aria-label="Remove">✕</button>
      </div>
    </li>
  `).join("");
}

function escHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function buildChips() {
  const container = document.getElementById("quick-chips");
  container.innerHTML = PRESETS.map((p, i) =>
    `<button class="chip" onclick="addEntry(PRESETS[${i}])">${p.name} · ${p.cal}kcal</button>`
  ).join("");
}

buildChips();
render();
