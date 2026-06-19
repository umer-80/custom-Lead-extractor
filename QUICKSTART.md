# ⚡ Quick Start Guide - Sentinel AI Lead Extractor

## 🚀 Get Running in 5 Minutes

### Step 1: Clone & Navigate
```bash
git clone https://github.com/umer-80/custom-Lead-extractor.git
cd custom-Lead-extractor
```

### Step 2: Install Dependencies
```bash
pip install -r Requirements/requirements.txt
playwright install chromium
```

### Step 3: Configure API Keys
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Gemini API keys:
```env
GEMINI_API_KEY=your_key_here
```

**Where to get keys:**
- Visit: https://makersuite.google.com/app/apikey
- Create 3-5 free keys from different Google accounts
- Format: `key1,key2,key3` (comma-separated)

### Step 4: Run Your First Hunt
```bash
python sentinel.py
```

**Follow the prompts:**
1. Niche: `Dentist`
2. Location: `Austin, TX`
3. Mode: `Commander (Radius)`
4. Radius: `30km`
5. Goal: `20`

**Expected Output:**
```
✔ Engine Online (3 API Keys Loaded)
─── Initiating Autonomous Sweep ───
🧭 Navigator plotting course around Austin, TX...
✔ Course Set: Found 8 targets.

Navigate: Arriving at Downtown Austin (0/20)
[1/5] Scouting: Smile Dental Studio...
[2/5] Scouting: Bright Teeth Clinic...
...
📦 Dispatching Batch of 10 for AI Analysis...

MISSION COMPLETE. 23 gold mines saved to leads_v4_Dentist_Austin_TX.csv
```

---

## 📁 What Files Are Generated?

### `leads_v4_Dentist_Austin_TX.csv`
Your main output with columns:
- Business Name
- Lead Status (Gold Mine / Broken Pro / Optimized)
- Phone
- Socials
- Silent Pain (AI insight)
- Battle Plan (what to sell)
- Hook (cold email opener)

### `history.json`
Deduplication database - tracks all scraped Place IDs to avoid re-analyzing.

---

## 🎯 Example Commands

### Single Location (Fast)
```bash
python src/main.py "Gym" "London"
```

### Radius Hunt (Thorough)
```bash
python src/main.py "Coffee Shop" "Berlin, Germany" --radius 50km --goal 100
```

### Interactive Mode (Recommended for First Use)
```bash
python sentinel.py
```

---

## ⚠️ Troubleshooting

### "No GEMINI_API_KEY found"
**Fix:** Make sure `.env` file exists and has your key(s).

### "Playwright not installed"
**Fix:** Run `playwright install chromium`

### "No leads found"
**Possible causes:**
- Niche too specific (try "Dentist" instead of "Pediatric Orthodontist")
- Location too small (try nearby city)
- Google rate limiting (wait 5 minutes and retry)

### Rate Limit Errors (429)
**Fix:** Add more API keys to `.env` (comma-separated):
```env
GEMINI_API_KEY=key1,key2,key3,key4,key5
```

---

## 💡 Pro Tips

1. **Best Niches**: Local service businesses work best
   - ✅ Dentists, Gyms, Salons, Plumbers, Lawyers
   - ❌ Walmart, McDonald's (chains have corporate sites)

2. **Optimal Radius**: 
   - Big cities: 10-20km
   - Suburbs: 30-50km
   - Rural: 50-100km

3. **Lead Goals**: 
   - Testing: 10-20 leads
   - Real hunt: 50-100 leads
   - Enterprise: 200+ (use multiple keys)

4. **Running Speed**:
   - ~5 leads/minute (single key)
   - ~30 leads/minute (5+ keys)

---

## 📊 Understanding Your Results

### Priority 1: "Gold Mine" (9-10/10)
**Profile:** High reviews, NO website  
**Why Valuable:** Easy win - they need a landing page + booking system ASAP  
**Close Rate:** ~15-20%

### Priority 2: "Broken Pro" (7-8/10)
**Profile:** Has website but broken SSL, outdated, or not mobile  
**Why Valuable:** Reputation at risk, technical debt is costing them money  
**Close Rate:** ~8-12%

### Priority 3: "Optimized" (1-3/10)
**Profile:** Modern website, all systems working  
**Action:** Skip or offer advanced services (AI chatbots, automation)  
**Close Rate:** ~2-4%

---

## 🔄 Updating the Project

```bash
cd custom-Lead-extractor
git pull origin main
pip install -r Requirements/requirements.txt --upgrade
```

---

## 📞 Support

- **Issues:** https://github.com/umer-80/custom-Lead-extractor/issues
- **Discussions:** https://github.com/umer-80/custom-Lead-extractor/discussions

---

## 🎉 You're Ready!

Run `python sentinel.py` and start finding gold mine leads!

**Next Steps:**
1. Export your first CSV
2. Review the AI-generated hooks
3. Start outreach with personalized emails
4. Track conversion rates

Happy hunting! 🎯
