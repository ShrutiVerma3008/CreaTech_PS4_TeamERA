# FormOptiX 🏗️

**Intelligent Formwork & Bill-of-Quantities Optimizer**
*CreaTech '26 · L&T · Problem Statement 4 · #JustLeap*

---

## 🎯 The Headache We're Trying to Cure

If you've ever worked on a high-rise construction site, you know about formwork—the temporary moulds we pour concrete into to build walls, slabs, and columns. It might just be temporary, but **formwork eats up 7–10% of the total construction budget**. It's easily one of the biggest controllable costs on a project.

But here's the crazy part: planning for it is still mostly done by hand. 
- Engineers often just eyeball the peak demand and order a bunch of extra panels "just in case."
- No one really has the time to sit down and mathematically check which floors are similar enough to share the exact same panels.
- Panels get ordered way too early and just sit in the yard, burning through rental and holding costs.
- Then, the architect changes the design mid-project, and those expensive panels you just bought? They become useless scrap.
- To make matters worse, Site A might have panels rotting in a yard while Site B (just across town) is out buying brand-new ones.

**We think it's time to fix this. That's where FormOptiX comes in.**

---

## 💡 How FormOptiX Helps

Think of FormOptiX as a **GPS for your formwork**. It's a smart, data-driven tool that looks at your building's geometry, predicts exactly what you'll need each week, and tells you **what to buy, when to buy it, and what you can reuse.**

We built the system around four core "brains":

### 1. 🔵 The Repetition Engine (Finding Patterns)
The app scans your BIM data or Excel schedules. Instead of guessing, it uses a clever machine-learning algorithm (called DBSCAN) to figure out which floors are "standard" (your typical tower floors) and which are "unique" (like the podium or roof). It then gives you a **Repetition Score**—telling you exactly what percentage of your building can share the same standard set of panels.

> **Why you'll love this:** If your score is 80%, you know that 80% of your floors can share the exact same formwork kit. The app even auto-generates the exact Bill of Materials (BOM) you need for that kit.

### 2. 🟢 The Dynamic BoQ Optimizer (Smart Buying)
Instead of ordering everything upfront, FormOptiX acts like a financial planner. It runs a **52-week mathematical optimization** to balance two things: the cost of buying new panels versus the cost of letting them sit idle in a yard. The result? A week-by-week shopping list that is mathematically guaranteed to save you the most money.

> **Why you'll love this:** No more ordering "just in case." You'll know exactly when to pull the trigger on an order and what to carry over to the next floor.

### 3. 🔴 Design Freeze Intelligence (The Safety Net)
This might be our favorite feature. When you upload a new design, the app calculates a **Design Instability (DI) Index**. Basically, it checks how much the floor layouts are changing between revisions. If the design is still shifting a lot (DI > 15%), FormOptiX throws up a **HALT** warning, telling you to wait before buying in bulk.

> **Why you'll love this:** You'll never accidentally order 500 panels right before the architect decides to move all the windows. It physically protects you from creating scrap.

### 4. 🌍 Cross-Site Portfolio Matching (Sharing is Caring)
If you're a massive company managing dozens of sites, idle panels are a huge waste. FormOptiX can scan your entire enterprise portfolio, find unused formwork at Site A, and match it to an upcoming need at Site B. 

> **Why you'll love this:** For a company like L&T, shuffling existing inventory around instead of buying fresh could easily save ₹10-20 Crores a year.

---

## 📊 Real-World Impact

So, what does this actually look like on a standard ₹500 Crore residential tower?

| Metric | The Old Way | The FormOptiX Way | The Win |
|--------|-----------------|-----------------|-------------|
| **Panel Utilization** | 60–65% | 82–87% | **+22% better usage** |
| **Time to generate BoQ** | 3–5 days | Under 4 hours | **90% faster** |
| **Excess Inventory** | 12–18% of BoQ | 4–6% | **65% less waste** |
| **Carrying Costs** | ₹3–5 Cr | ₹1.5–2 Cr | **Cut in half** |
| **Total Formwork Savings**| — | **₹12–18 Cr** | **12–15% cheaper overall** |

### The Short Version
> *"FormOptiX is your formwork GPS. It tells you what to reuse, when to order, and exactly how much cash you're going to save—all before a single drop of concrete is poured."*

---

## 🧠 The Science Behind the Magic

We promise this isn't just a fancy spreadsheet. Every recommendation FormOptiX makes is backed by real-world civil engineering and operations research:

| Feature | What It Does | The Nerd Stuff (Academic Basis) |
|-----------|-------------|----------------|
| **DBSCAN Clustering** | Groups similar floors together and ignores the weirdly shaped ones. | Ester et al. (1996), KDD-96 |
| **Linear Programming** | Crunches the numbers to find the absolute cheapest 52-week buying plan. | Hillier & Lieberman (2021), Ch.3 |
| **Physical Constraints** | Makes sure we account for the time it takes concrete to cure before stripping panels. | Hanna (1998), Ch.4; ACI 347R-14 S.5 |
| **Design Freeze Index** | Hits the brakes on procurement if the design is too chaotic. | Ibbs (1997), J. Constr. Eng. Mgmt |
| **Cross-Site Matching** | Plays matchmaker between idle panels at one site and demands at another. | Dania et al. (2015), JEDT |

---

## 🗺️ Where We're Heading

We built this as a hackathon prototype, but we have big plans to make it a production-ready tool:

| Phase | When | What We're Doing | The Goal |
|-------|---------|-------------|----------------|
| **Phase 0** | 0–3 months | Python prototype (You are here!) | Prove the math works and win CreaTech '26 🏆 |
| **Phase 1** | 3–9 months | Pilot on a real L&T tower | Prove we can cut formwork costs by at least 12% |
| **Phase 2** | 9–18 months | Connect to BIM, ERP, and RFID tags | Save ₹15–20 Cr across 10 active projects |
| **Phase 3** | 18–36 months | Launch as a SaaS product | Hit ₹5 Cr in recurring revenue with 3 major builders |

---

## ⚔️ How We Compare

There are a lot of tools out there, but none of them do exactly what we do:

| Feature | Primavera P6 | SAP ERP | Revit/BIM | **FormOptiX ★** |
|---------|:---:|:---:|:---:|:---:|
| Project Scheduling | ✅ | ❌ | ❌ | ✅ |
| Formwork Procurement Planning | ❌ | ✅ | ❌ | ✅ |
| Repetition Intelligence | ❌ | ❌ | ❌ | ✅ |
| Design Freeze Guard | ❌ | ❌ | ❌ | ✅ |
| Cross-Site Portfolio Optimization | ❌ | ❌ | ❌ | ✅ |
| Automated Kit BOM Generation | ❌ | ❌ | ❌ | ✅ |

FormOptiX is the **only tool** that tracks formwork all the way from analyzing the floor shapes to shuffling panels between different construction sites.

---

## 🚀 Let's Get Started

Want to take it for a spin? You can run the dashboard on your own machine in three easy steps.

### What you need:
Just make sure you have Python 3.9 (or newer) installed.

### Step 1: Install the boring stuff
```bash
pip install -r requirements.txt
```
*(Optional: run `pip install reportlab` if you want to export fancy PDF reports later!)*

### Step 2: Start the engine
```bash
streamlit run frontend/app.py
```
A browser window should pop right up at `http://localhost:8501`.

### Step 3: Look around!
The app starts in **Synthetic Demo Mode**, building a fake 20-floor tower for you to play with. Check out the 6 main tabs:

| Tab | What to look for |
|-----|--------------|
| 🎯 **Repetition Analysis** | See the clusters, check your score, and grab your Kit BOM. |
| 💰 **Cost Optimization** | See the math in action and watch the ROI waterfall chart. |
| 📦 **Inventory & Forecast** | Check the 52-week inventory curve to see when you'll be short on panels. |
| 📐 **Building Data** | Geek out over the raw floor geometry data. |
| 🗺️ **Roadmap & Impact** | Review our future plans and competitive edge. |
| 🌍 **Cross-Site Portfolio** | Watch the system reallocate idle panels between different sites live! |

### Step 4: Try your own data (If you're feeling adventurous)
1. Select **"Real Site Data"** in the left menu.
2. Upload one of the Excel files we left for you in the `data/` folder.
3. If your columns have weird names, don't worry—the app has a visual mapper to help you line them up.
4. Hit **Run FormOptiX Engine** and watch it go!

---

## 📋 What the Excel Data Should Look Like

If you want to feed it your own custom Excel file, here's how to format the columns (though the app will help you map them if you get it wrong):

**Sheet: `floors`**
| floor_id | floor_name | floor_type | slab_area_sqm | wall_length_m | column_count | beam_count |
|----------|------------|------------|---------------|---------------|--------------|------------|
| F01 | Ground Floor | Podium | 2400 | 640 | 48 | 56 |
| F04 | 4th Floor | Typical | 850 | 420 | 24 | 28 |

**Sheet: `schedule`**
| week | wall_panels_demand | slab_panels_demand | col_panels_demand |
|------|-------------------|-------------------|------------------|
| 1 | 150 | 280 | 80 |
| 2 | 210 | 310 | 95 |

---

> 👨‍💻 **Are you a developer or technical judge?**
> We built this right. Check out our [**README_for_nerds.md**](README_for_nerds.md) to dive into the clean architecture, the math behind the algorithms, and how to extend the code!
