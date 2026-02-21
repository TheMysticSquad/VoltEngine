import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. DATA MANAGER (In-Memory DB)
# ==========================================
class DataManager:
    @staticmethod
    def init():
        if 'categories' not in st.session_state:
            st.session_state.categories = {
                "DS-II": {
                    "cat_id": "DS-II", "name": "Domestic Rural (DS-II)", "fixed_charge": 120.0,
                    "demand_rate": 250.0, "subsidy_rate": 1.00, "duty_rate": 0.05,
                    "slabs": [{"Upto KWh": 50, "Rate (₹)": 3.10}, {"Upto KWh": 100, "Rate (₹)": 3.60}, {"Upto KWh": 999999, "Rate (₹)": 4.10}]
                },
                "NDS-I": { 
                    "cat_id": "NDS-I", "name": "Non-Domestic Urban (NDS-I)", "fixed_charge": 250.0,
                    "demand_rate": 400.0, "subsidy_rate": 0.00, "duty_rate": 0.08,
                    "slabs": [{"Upto KWh": 100, "Rate (₹)": 5.50}, {"Upto KWh": 999999, "Rate (₹)": 6.50}]
                }
            }
        if 'consumers' not in st.session_state: st.session_state.consumers = {}
        if 'ledger' not in st.session_state: st.session_state.ledger = []
        if 'readings' not in st.session_state: st.session_state.readings = []
        if 'settlements' not in st.session_state: st.session_state.settlements = []

    @staticmethod
    def get_tariff(cat_id): return st.session_state.categories.get(cat_id)
    @staticmethod
    def save_consumer(consumer): st.session_state.consumers[consumer.consumer_id] = consumer
    @staticmethod
    def get_consumer(c_id): return st.session_state.consumers.get(c_id)
    @staticmethod
    def add_reading_log(data): st.session_state.readings.append(data)
    @staticmethod
    def add_ledger_entry(date, c_id, desc, amount, type_, balance):
        st.session_state.ledger.append({
            "Date": str(date), "Consumer ID": c_id, "Description": desc,
            "Amount (₹)": float(amount), "Type": type_, "Running Balance (₹)": float(balance),
            "Timestamp": datetime.now().strftime("%H:%M:%S")
        })

# ==========================================
# 2. CORE LOGIC & ENGINES
# ==========================================

class Consumer:
    def __init__(self, consumer_id, name, address, category_id, wallet, arrear, load, installment, initial_reading):
        self.consumer_id = consumer_id
        self.name = name
        self.address = address
        self.category_id = category_id
        self.wallet_balance = float(wallet)
        self.arrear_balance = float(arrear)
        self.load_kw = float(load)
        self.installment = installment # Format: {"daily": 20.0, "recovery_days": 365}
        self.last_reading = float(initial_reading)
        self.status = "ACTIVE"
        self.deficit_balance = 0.0
        self.negative_days = 0 
        self.amendments = []

class PaymentEngine:
    @staticmethod
    def process_recharge(consumer, amount):
        """Handles Wallet Top-ups and Auto-Reconnection logic"""
        consumer.wallet_balance += amount
        remarks = "Wallet Recharge"
        
        if consumer.wallet_balance >= 0 and consumer.status == "DISCONNECTED":
            consumer.status = "ACTIVE"
            consumer.negative_days = 0
            remarks += " (Auto-Reconnected)"
            consumer.amendments.append({"Date": datetime.now().strftime("%Y-%m-%d"), "Type": "Status", "Details": "DISCONNECTED -> ACTIVE"})
        elif consumer.wallet_balance >= 0 and consumer.negative_days > 0:
            consumer.negative_days = 0
            remarks += " (Warning Reset)"
            
        DataManager.save_consumer(consumer)
        DataManager.add_ledger_entry(datetime.now().date(), consumer.consumer_id, remarks, amount, "CREDIT", consumer.wallet_balance)
        return consumer.wallet_balance

    @staticmethod
    def process_arrear_payment(consumer, amount, recovery_days):
        """Processes partial/full arrear payments and recalculates installments."""
        paid_amount = min(amount, consumer.arrear_balance)
        consumer.arrear_balance -= paid_amount
        
        if consumer.arrear_balance > 0:
            new_daily = round(consumer.arrear_balance / recovery_days, 2)
            consumer.installment = {"daily": new_daily, "recovery_days": recovery_days}
        else:
            consumer.installment = {"daily": 0.0, "recovery_days": 0}
            
        DataManager.save_consumer(consumer)
        DataManager.add_ledger_entry(datetime.now().date(), consumer.consumer_id, f"Arrear Payment Received", 0.0, "INFO", consumer.wallet_balance)
        return paid_amount

class MigrationEngine:
    @staticmethod
    def migrate(old_acc, name, address, category_id, old_arrear, security_dep, load, closing_reading, recovery_days=365):
        net_balance = float(old_arrear) - float(security_dep)
        new_wallet = abs(net_balance) if net_balance < 0 else 0.0
        new_arrear = net_balance if net_balance > 0 else 0.0
        inst_amt = round(new_arrear / recovery_days, 2) if new_arrear > 0 else 0
        
        c = Consumer(f"PRE-{old_acc}", name, address, category_id, new_wallet, new_arrear, load, {"daily": inst_amt, "recovery_days": recovery_days}, closing_reading)
        if new_wallet > 0:
            DataManager.add_ledger_entry(datetime.now().date(), c.consumer_id, "Opening Balance", new_wallet, "CREDIT", new_wallet)
        return c

class SlabEngine:
    @staticmethod
    def calculate_energy_charge(units, slabs):
        sorted_slabs = sorted(slabs, key=lambda x: x['Upto KWh'])
        charge = 0.0
        remaining_units = units
        prev_limit = 0
        for slab in sorted_slabs:
            slab_size = slab['Upto KWh'] - prev_limit
            if remaining_units <= 0: break
            units_in_slab = min(remaining_units, slab_size)
            charge += units_in_slab * slab['Rate (₹)']
            remaining_units -= units_in_slab
            prev_limit = slab['Upto KWh']
        return charge

class PrepaidDailyBilling:
    def run(self, consumer, current_kwh, max_demand, date_str, is_meter_change=False):
        tariff = DataManager.get_tariff(consumer.category_id)
        if not tariff: return {"error": "Invalid Tariff Category"}

        remarks = []
        units_consumed = current_kwh - consumer.last_reading
        if units_consumed < 0: return {"error": "Negative Consumption"}
        
        base_rate = min(tariff['slabs'], key=lambda x: x['Rate (₹)'])['Rate (₹)']
        gross_ec = units_consumed * base_rate
        subsidy = units_consumed * tariff.get('subsidy_rate', 0.0)
        net_ec = max(0, gross_ec - subsidy)
        
        fc = tariff['fixed_charge'] / 30.0
        duty = (net_ec + fc) * tariff['duty_rate']
        
        penalty = 0.0
        if max_demand > consumer.load_kw:
            excess = max_demand - consumer.load_kw
            penalty = excess * tariff['demand_rate'] * 1.5 / 30.0
            remarks.append(f"Excess Load (+{excess}KW)")

        inst = 0.0
        if consumer.arrear_balance > 0:
            inst = min(consumer.installment.get('daily', 0), consumer.arrear_balance)
            if inst == consumer.arrear_balance: remarks.append("Arrear Cleared!")

        total_deduction = net_ec + fc + duty + penalty + inst
        
        consumer.wallet_balance -= total_deduction
        consumer.arrear_balance -= inst
        if not is_meter_change:
            consumer.last_reading = current_kwh
        
        # D&R State Machine
        if consumer.wallet_balance < 0:
            consumer.negative_days += 1
            if consumer.negative_days == 1: remarks.append("SMS: 1st Negative Alert")
            elif consumer.negative_days == 2: remarks.append("SMS: 2nd Negative Alert")
            elif consumer.negative_days == 3: remarks.append("SMS: Pre-Disconnection Notice")
            elif consumer.negative_days == 4:
                consumer.status = "DISCONNECTED"
                remarks.append("ACTION: Power Disconnected")
                consumer.amendments.append({"Date": date_str, "Type": "Status", "Details": "ACTIVE -> DISCONNECTED"})
            else:
                remarks.append("Status: DISCONNECTED")
        
        desc = "Daily DCC Bill" if not is_meter_change else "Meter Changeout Final Bill"
        DataManager.add_ledger_entry(date_str, consumer.consumer_id, desc, -total_deduction, "DEBIT", consumer.wallet_balance)
        
        log_entry = {
            "Date": date_str, "Consumer ID": consumer.consumer_id, "Units": units_consumed, "Max MD": max_demand,
            "Gross EC": round(gross_ec, 2), "Subsidy": round(subsidy, 2), "Net EC": round(net_ec, 2), 
            "FC": round(fc, 2), "Duty": round(duty, 2), "Excess MD": round(penalty, 2), "Inst": round(inst, 2),
            "Total": round(total_deduction, 2), "Wallet": round(consumer.wallet_balance, 2),
            "Remarks": ", ".join(remarks) if remarks else "-"
        }
        DataManager.add_reading_log(log_entry)
        DataManager.save_consumer(consumer)
        return log_entry

class MonthlySettlementEngine:
    @staticmethod
    def run_settlement(consumer, month_str):
        tariff = DataManager.get_tariff(consumer.category_id)
        logs = [l for l in st.session_state.readings if l['Consumer ID'] == consumer.consumer_id and month_str in str(l['Date'])]
        if not logs: return {"status": "FAILED", "reason": "No logs for month"}
            
        total_units = sum(l['Units'] for l in logs)
        
        gross_ec = SlabEngine.calculate_energy_charge(total_units, tariff['slabs'])
        total_subsidy = total_units * tariff.get('subsidy_rate', 0.0)
        net_ec = max(0, gross_ec - total_subsidy)
        
        fixed_charge = tariff['fixed_charge']
        duty = (net_ec + fixed_charge) * tariff['duty_rate']
        
        shadow_bill = net_ec + fixed_charge + duty
        daily_deducted = sum(l['Net EC'] + l['FC'] + l['Duty'] for l in logs)
        adjustment = shadow_bill - daily_deducted
        
        status = "SUCCESS"
        if adjustment != 0:
            if consumer.wallet_balance >= adjustment:
                consumer.wallet_balance -= adjustment
            else:
                consumer.deficit_balance += (adjustment - consumer.wallet_balance)
                consumer.wallet_balance = 0
                status = "DEFICIT"
                
            type_ = "DEBIT" if adjustment > 0 else "CREDIT"
            DataManager.add_ledger_entry(datetime.now().strftime("%Y-%m-%d"), consumer.consumer_id, 
                                         f"Monthly True-Up ({month_str})", -adjustment, type_, consumer.wallet_balance)

        DataManager.save_consumer(consumer)
        res = {
            "month": month_str, "consumer_id": consumer.consumer_id, "units": total_units,
            "shadow_bill": round(shadow_bill, 2), "daily_deducted": round(daily_deducted, 2),
            "adjustment": round(adjustment, 2), "status": status
        }
        st.session_state.settlements.append(res)
        return res

# ==========================================
# 3. STREAMLIT UI
# ==========================================
st.set_page_config(page_title="VoltEngine Pro", layout="wide", page_icon="⚡")
DataManager.init()

st.title("⚡ VoltEngine: Billing & Recovery Simulator")

active_consumers = list(st.session_state.consumers.keys())
selected_c_id = st.sidebar.selectbox("Active Consumer", ["Select"] + active_consumers)

tabs = st.tabs(["⚙️ Masters", "🔄 Migration", "👤 Profile", "🛠️ Services", "📟 Readings", "📊 DCC & Ledger", "💰 Financial Desk", "📅 Settlement"])

# --- TAB 1: CATEGORY ---
with tabs[0]:
    st.write("Active Tariff Categories (Includes NDS)")
    for key, val in st.session_state.categories.items():
        with st.expander(f"{val['name']} ({key})"):
            st.json(val)

# --- TAB 2: MIGRATION ---
with tabs[1]:
    c1, c2, c3 = st.columns(3)
    acc = c1.text_input("Old Acc", "KNO-001")
    cat = c1.selectbox("Category", list(st.session_state.categories.keys()))
    arr = c2.number_input("Arrears", 3000.0)
    sec = c2.number_input("Security Dep", 1000.0)
    ld = c3.number_input("Load (KW)", 2.0)
    rd = c3.number_input("Closing Read", 500.0)
    
    if st.button("Migrate"):
        c = MigrationEngine.migrate(acc, "John Doe", "Bihar", cat, arr, sec, ld, rd)
        DataManager.save_consumer(c)
        st.success(f"Migrated: {c.consumer_id}")

# --- TAB 3: PROFILE ---
with tabs[2]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        st.header("Consumer Profile")
        colA, colB, colC, colD = st.columns(4)
        colA.markdown(f"**Category:** {c.category_id}")
        colA.markdown(f"**Load:** {c.load_kw} KW")
        colB.metric("Wallet", f"₹{c.wallet_balance:.2f}")
        colB.metric("Arrear", f"₹{c.arrear_balance:.2f}")
        
        status_color = "green" if c.status == "ACTIVE" else "red"
        colC.markdown(f"**Status:** :{status_color}[{c.status}]")
        colC.markdown(f"**Negative Days:** {c.negative_days}")
        
        colD.markdown("**Installment Plan:**")
        colD.info(f"₹{c.installment.get('daily', 0)}/day ({c.installment.get('recovery_days', 0)} days left)")

        if c.amendments:
            st.subheader("📝 Amendment & Event History")
            st.dataframe(pd.DataFrame(c.amendments), width="stretch")

# --- TAB 4: SERVICES ---
with tabs[3]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        st.header("Service Requests (Amendments)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Master Data Change")
            new_load = st.number_input("New Load (KW)", value=c.load_kw)
            new_cat = st.selectbox("New Category", list(st.session_state.categories.keys()), index=list(st.session_state.categories.keys()).index(c.category_id))
            
            if st.button("Apply Master Data Change"):
                if new_load != c.load_kw or new_cat != c.category_id:
                    c.amendments.append({"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "Master Data", "Details": f"{c.load_kw}KW/{c.category_id} -> {new_load}KW/{new_cat}"})
                    c.load_kw, c.category_id = new_load, new_cat
                    DataManager.save_consumer(c)
                    st.success("Updated! Next DCC will use new parameters.")

        with col2:
            st.subheader("2. Meter Replacement (MCO)")
            final_read = st.number_input("Final Reading of OLD Meter", min_value=c.last_reading, value=c.last_reading + 5)
            initial_read = st.number_input("Initial Reading of NEW Meter", value=0.0)
            mco_date = st.date_input("MCO Date")
            
            if st.button("Execute Meter Replacement"):
                res = PrepaidDailyBilling().run(c, final_read, c.load_kw, str(mco_date), is_meter_change=True)
                if "error" not in res:
                    c.last_reading = initial_read
                    c.amendments.append({"Date": str(mco_date), "Type": "Meter Replacement", "Details": f"Old Final: {final_read} | New Initial: {initial_read}"})
                    DataManager.save_consumer(c)
                    st.success("Meter Replaced! Final bill generated and new reading initialized.")

# --- TAB 5: READINGS ---
with tabs[4]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        col1, col2 = st.columns(2)
        r_date = col1.date_input("Date")
        curr_read = col2.number_input("Reading", min_value=c.last_reading, value=c.last_reading + 8)
        max_md = col2.number_input("Max Demand", value=c.load_kw)
        
        if st.button("Run DCC"):
            res = PrepaidDailyBilling().run(c, curr_read, max_md, str(r_date))
            if "error" not in res: st.success("DCC Processed!")

# --- TAB 6: DCC & LEDGER ---
with tabs[5]:
    if selected_c_id != "Select":
        dcc_tab, ledger_tab = st.tabs(["📊 Detailed DCC View", "📒 Financial Ledger"])
        
        with dcc_tab:
            c_logs = [l for l in st.session_state.readings if l['Consumer ID'] == selected_c_id]
            if c_logs: st.dataframe(pd.DataFrame(c_logs), width="stretch")
            
        with ledger_tab:
            c_ledg = [l for l in st.session_state.ledger if l['Consumer ID'] == selected_c_id]
            if c_ledg:
                df_ledg = pd.DataFrame(c_ledg)
                def color_type(val):
                    color = 'green' if val == 'CREDIT' else 'red' if val == 'DEBIT' else 'gray'
                    return f'color: {color}'
                st.dataframe(df_ledg.style.map(color_type, subset=['Type']), width="stretch")

# --- TAB 7: FINANCIAL DESK ---
with tabs[6]:
    st.header("Financial Desk")
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        pay_type = st.radio("Payment Type", ["Wallet Recharge", "Arrear Clearance"])
        
        if pay_type == "Wallet Recharge":
            st.subheader("Top-Up Wallet (Auto-Reconnects if Disconnected)")
            st.write(f"Current Wallet: ₹{c.wallet_balance:.2f}")
            w_amt = st.number_input("Recharge Amount (₹)", value=500.0)
            if st.button("Process Recharge"):
                PaymentEngine.process_recharge(c, w_amt)
                st.success(f"Recharged! New Wallet: ₹{c.wallet_balance:.2f}")
                
        elif pay_type == "Arrear Clearance":
            st.subheader("Restructure Installment & Clear Arrears")
            st.error(f"Total Outstanding Arrear: ₹{c.arrear_balance:.2f}")
            
            a_amt = st.number_input("Payment Amount (₹)", max_value=c.arrear_balance, value=min(1000.0, c.arrear_balance))
            st.markdown("### Installment Table Logic (Post-Payment)")
            rec_days = st.slider("New Recovery Period (Days) for Remaining Arrear", min_value=30, max_value=730, value=365)
            
            projected_remaining = c.arrear_balance - a_amt
            projected_daily = projected_remaining / rec_days if projected_remaining > 0 else 0
            st.info(f"If you pay ₹{a_amt} today, the remaining arrear (₹{projected_remaining:.2f}) will trigger a new daily deduction of **₹{projected_daily:.2f}/day**.")
            
            if st.button("Process Arrear Payment"):
                paid = PaymentEngine.process_arrear_payment(c, a_amt, rec_days)
                st.success(f"Successfully processed ₹{paid} towards arrears. New daily installment set to ₹{c.installment['daily']}.")

# --- TAB 8: SETTLEMENT ---
with tabs[7]:
    if selected_c_id != "Select":
        m_sel = st.selectbox("Month", ["2026-02", "2026-03"])
        if st.button("Run Monthly Settlement"):
            res = MonthlySettlementEngine.run_settlement(DataManager.get_consumer(selected_c_id), m_sel)
            st.json(res)