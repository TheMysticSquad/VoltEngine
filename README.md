# ⚡ VoltEngine
**The Universal Utility Billing Framework**

VoltEngine is an industry-ready Python library designed to automate complex electricity billing cycles. From simple domestic slab rates (LT) to complex industrial demand charges (HT), VoltEngine provides a modular math-heavy core to ensure zero-error invoicing.

## 🎯 Domain Coverage
- **LT Postpaid:** Residential/Commercial slab-based billing.
- **LT Prepaid:** Real-time credit-to-energy conversion logic.
- **HT (High Tension):** Industrial billing featuring Demand Charges, Power Factor (PF) adjustments, and Time-of-Day (ToD) tariffs.

## ⚙️ Core Logic Flow
The engine processes data through a structured pipeline to ensure compliance with regulatory standards:

1. **Input Layer:** Consumes KWh (Active), KVAh (Apparent), and MD (Maximum Demand).
2. **Tariff Resolver:** Matches consumer type to specific state/utility rate cards.
3. **Calculation Engine:** Processes fixed charges, energy charges, and penalties.
4. **Taxation Module:** Applies Duty, GST, and Surcharges.
5. **Output Layer:** Generates a structured JSON objects ready for PDF invoicing or API consumption.



## 🛠️ Tech Stack
- **Engine:** Python 3.10+ (Logic & Math)
- **Validation:** Pydantic (Data integrity)
- **API Layer:** FastAPI (High-speed integration)
- **UI/Simulator:** Streamlit (For real-time billing simulation)
