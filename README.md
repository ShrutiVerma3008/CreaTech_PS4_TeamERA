# FormOptiX 🏗️

**Intelligent Formwork & Bill-of-Quantities Optimizer**
*CreaTech '26 · L&T · Problem Statement 4 · #JustLeap*

---

## 🎯 Problem Statement

Formwork—the temporary moulds into which concrete is poured to build walls, slabs, and columns—is a critical component of high-rise construction. Although temporary, **formwork constitutes approximately 7–10% of the total construction budget**, making it one of the most significant controllable costs on a project.

Currently, the planning and procurement of formwork rely heavily on manual estimation processes:
- Engineers often estimate peak demand visually and order surplus panels to mitigate risk.
- Rigorous mathematical analysis to identify floors with geometric similarities for panel reuse is rarely performed due to time constraints.
- Panels are frequently procured prematurely, accumulating rental and holding costs while sitting idle in inventory yards.
- Mid-project design modifications by architects can render previously procured, expensive panels unusable, generating unnecessary scrap.
- Across large portfolios, inventory is often siloed, meaning one site might have unused panels degrading in storage while another site purchases new inventory.

**FormOptiX addresses these inefficiencies through a data-driven, intelligent approach to formwork management.**

---

## 💡 Proposed Solution: FormOptiX

FormOptiX serves as a **strategic intelligence tool for formwork management**. By analyzing building geometry, it accurately forecasts weekly requirements, providing actionable insights on **procurement timing, quantities, and reuse opportunities.**

The system is built upon four core architectural pillars:

### 1. 🔵 Repetition Analysis Engine (Geometric Pattern Recognition)
The application ingests Building Information Modeling (BIM) data or tabular schedules. It employs the **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** machine learning algorithm to classify floors into "standard" (typical tower floors) and "unique" (e.g., podiums or roofs) categories. This produces a **Repetition Score**, quantifying the percentage of the building that can utilize a standardized formwork kit.

> **Impact:** An 80% Repetition Score indicates that 80% of the structure can share identical formwork. The system automatically generates the precise Bill of Materials (BOM) required for this optimized kit.

### 2. 🟢 Dynamic BoQ Optimizer (Financial & Procurement Strategy)
Moving beyond static, upfront ordering, FormOptiX functions as a dynamic financial planning tool. It executes a **52-week linear programming optimization** to balance the capital expenditure of new panels against the carrying costs of idle inventory. The output is an optimized, week-by-week procurement schedule mathematically designed to minimize total costs.

> **Impact:** Eliminates the need for speculative ordering. Project managers receive precise timelines for procurement and inter-floor material transfer.

### 3. 🔴 Design Freeze Intelligence (Risk Mitigation)
To address the risk of mid-project changes, FormOptiX calculates a **Design Instability (DI) Index** upon the upload of revised designs. This metric evaluates the variance between layout iterations. If the design remains highly volatile (e.g., DI > 15%), the system issues a **HALT** recommendation, advising against bulk procurement.

> **Impact:** Prevents the premature acquisition of materials that may become obsolete due to architectural modifications, actively reducing material waste.

### 4. 🌍 Cross-Site Portfolio Matching (Enterprise Resource Allocation)
For organizations managing multiple simultaneous projects, FormOptiX provides enterprise-level visibility. It scans the overarching portfolio to identify idle formwork at one site and matches it to projected demand at another.

> **Impact:** Maximizes asset utilization. For enterprise operations, reallocating existing inventory rather than procuring new materials can yield substantial annual savings.

---

## 📊 Projected Business Impact

The implementation of FormOptiX on a standard large-scale residential project demonstrates significant potential for optimization:

| Metric | Traditional Approach | FormOptiX Optimization | Performance Gain |
|--------|-----------------|-----------------|-------------|
| **Panel Utilization** | 60–65% | 82–87% | **+22% Improvement** |
| **BoQ Generation Time** | 3–5 Days | < 4 Hours | **90% Reduction** |
| **Excess Inventory** | 12–18% of BoQ | 4–6% | **65% Reduction in Waste** |
| **Carrying Costs** | High Baseline | Optimized Scheduling | **Approx. 50% Reduction** |
| **Total Formwork Costs**| Standard Expenditure | **Optimized Efficiency** | **12–15% Overall Cost Savings** |

### Executive Summary
> *"FormOptiX serves as a comprehensive formwork intelligence platform. It provides actionable directives on material reuse, procurement timing, and cost optimization—delivering verifiable savings before construction commences."*

---

## 🧠 Technical Methodology

The recommendations generated by FormOptiX are grounded in rigorous civil engineering principles and operations research methodologies:

| Module | Functionality | Academic & Technical Basis |
|-----------|-------------|----------------|
| **DBSCAN Clustering** | Aggregates geometrically similar floors while isolating anomalies. | Ester et al. (1996), KDD-96 |
| **Linear Programming** | Computes the optimal 52-week procurement strategy to minimize cost. | Hillier & Lieberman (2021), Introduction to Operations Research |
| **Physical Constraints Modeling** | Integrates concrete curing times and stripping cycles into the planning model. | Hanna (1998); ACI 347R-14 |
| **Design Freeze Index** | Suspends procurement processes during periods of high design volatility. | Ibbs (1997), Journal of Construction Engineering and Management |
| **Cross-Site Matching Algorithm** | Optimizes the reallocation of idle inventory across multiple construction sites. | Dania et al. (2015), Journal of Engineering, Design and Technology |

---

## 🗺️ Project Roadmap

The current version serves as a robust proof-of-concept, with a clearly defined pathway to enterprise deployment:

| Phase | Timeline | Key Deliverables | Strategic Objective |
|-------|---------|-------------|----------------|
| **Phase 0** | 0–3 Months | Initial Python-based prototype (Current State). | Validate underlying mathematical models and demonstrate viability for CreaTech '26. |
| **Phase 1** | 3–9 Months | Pilot deployment on a live construction site. | Empirically validate the projected 12% reduction in formwork costs. |
| **Phase 2** | 9–18 Months | Integration with existing BIM, ERP systems, and RFID tracking. | Scale operations and achieve measurable savings across multiple active projects. |
| **Phase 3** | 18–36 Months | Commercialization as a SaaS solution. | Establish recurring revenue streams through enterprise adoption. |

---

## ⚔️ Competitive Advantage

FormOptiX provides specialized capabilities that are not currently addressed by standard industry software:

| Capability | Primavera P6 | SAP ERP | Revit/BIM | **FormOptiX** |
|---------|:---:|:---:|:---:|:---:|
| Project Scheduling | ✅ | ❌ | ❌ | ✅ |
| Formwork Procurement Planning | ❌ | ✅ | ❌ | ✅ |
| Repetition Intelligence | ❌ | ❌ | ❌ | ✅ |
| Design Freeze Guard | ❌ | ❌ | ❌ | ✅ |
| Cross-Site Portfolio Optimization | ❌ | ❌ | ❌ | ✅ |
| Automated Kit BOM Generation | ❌ | ❌ | ❌ | ✅ |

FormOptiX uniquely tracks the entire formwork lifecycle—from the initial analysis of floor geometry to the dynamic reallocation of panels across a multi-site portfolio.

---

## 🚀 Getting Started

The platform can be executed locally to evaluate its functionality.

### Prerequisites
- Python 3.9 or higher is required.

### Installation & Execution

1. **Install Dependencies:**
   Navigate to the project directory and install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(Optional: Execute `pip install reportlab` to enable PDF report generation capabilities.)*

2. **Launch the Application:**
   Start the Streamlit server:
   ```bash
   streamlit run frontend/app.py
   ```
   The application interface will automatically open in your default web browser at `http://localhost:8501`.

### Application Navigation
The system initializes in **Synthetic Demo Mode**, generating a simulated 20-story structure for evaluation purposes. The interface is organized into six primary modules:

| Module | Description |
|-----|--------------|
| 🎯 **Repetition Analysis** | Visualizes clustering results, displays the Repetition Score, and details the optimal Kit BOM. |
| 💰 **Cost Optimization** | Demonstrates the financial modeling and presents the Return on Investment (ROI) waterfall chart. |
| 📦 **Inventory & Forecast** | Illustrates the 52-week inventory projection, highlighting potential material shortages. |
| 📐 **Building Data** | Provides access to the raw geometric data underlying the analysis. |
| 🗺️ **Roadmap & Impact** | Outlines strategic future developments and comparative advantages. |
| 🌍 **Cross-Site Portfolio** | Simulates the dynamic reallocation of idle formwork across a multi-site enterprise. |

### Processing Custom Data
To evaluate the system using proprietary data:
1. Select **"Real Site Data"** from the navigation sidebar.
2. Upload a formatted Excel file (sample templates are provided in the `data/` directory).
3. Utilize the visual mapping interface to align custom column headers with system requirements.
4. Execute the **"Run FormOptiX Engine"** to initiate the analysis.

---

## 📋 Data Formatting Guidelines

When utilizing custom Excel datasets, the data should ideally conform to the following schema. (The application includes a column mapping utility to accommodate variations).

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

> 👨‍💻 **Technical Documentation**
> For an in-depth review of the system architecture, algorithmic implementations, and extensibility guidelines, please refer to the [**Technical Documentation (README_for_nerds.md)**](README_for_nerds.md).
