import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid

# ==========================================
# 1. DATA MANAGER (In-Memory DB)
# ==========================================
class DataManager:
    @staticmethod
    def init():
        if 'consumers' not in st.session_state:
            st.session_state.consumers = {}
        if 'ledger' not in st.session_state:
            st.session_state.ledger = []
        if 'readings' not in st.session_state:
            st.session_state.readings = [] 
        if 'settlements' not in st.session_state:
            st.session_state.settlements = []

    @staticmethod
    def save_consumer(consumer):
        st.session_state.consumers[consumer.consumer_id] = consumer
    
    @staticmethod
    def get_consumer(c_id):
        return st.session_state.consumers.get(c_id)

    @staticmethod
    def add_reading_log(data):
        st.session_state.readings.append(data)

    @staticmethod
    def add_ledger_entry(date, c_id, desc, amount, type_):
        st.session_state.ledger.append({
            "Date": str(date),
            "Consumer ID": c_id,
            "Description": desc,
            "Amount": float(amount),
            "Type": type_,
            "Timestamp": datetime.now().strftime("%H:%M:%S")
        })

    @staticmethod
    def add_settlement(data):
        st.session_state.settlements.append(data)

# ==========================================
# 2. CORE LOGIC
# ==========================================

class Consumer:
    def __init__(self, consumer_id, name, address, wallet, arrear, load, installment, initial_reading):
        self.consumer_id = consumer_id
        self.name = name
        self.address = address
        self.wallet_balance = float(wallet)
        self.arrear_balance = float(arrear)
        self.load_kw = float(load)
        self.installment = installment 
        self.last_reading = float(initial_reading)
        self.status = "ACTIVE"
        # Settlement Flags
        self.last_settlement_date = None
        self.deficit_balance = 0.0

class MigrationEngine:
    @staticmethod
    def migrate(old_acc, name, address, old_arrear, security_dep, load, closing_reading):
        net_balance = float(old_arrear) - float(security_dep)
        new_wallet = abs(net_balance) if net_balance < 0 else 0.0
        new_arrear = net_balance if net_balance > 0 else 0.0
        inst_amt = round(new_arrear / 365, 2) if new_arrear > 0 else 0
        
        return Consumer(f"PRE-{old_acc}", name, address, new_wallet, new_arrear, load, {"daily": inst_amt}, closing_reading)

class PrepaidDailyBilling:
    def run(self, consumer, current_kwh, max_demand, tariff, date_str):
        # ... (Daily Logic remains same for DCC) ...
        remarks = []
        units_consumed = current_kwh - consumer.last_reading
        if units_consumed < 0: return {"error": "Negative Consumption"}
        
        # Charges
        ec = units_consumed * tariff['rate']
        fc = tariff['fixed_charge'] / 30.0
        duty = (ec + fc) * tariff['duty_rate']
        
        penalty = 0.0
        if max_demand > consumer.load_kw:
            excess = max_demand - consumer.load_kw
            penalty = excess * tariff['demand_rate'] * 1.5 / 30.0
            remarks.append(f"Excess Load: +{excess} KW")

        inst = 0.0
        if consumer.arrear_balance > 0:
            inst = min(consumer.installment.get('daily', 0), consumer.arrear_balance)
            if inst == consumer.arrear_balance: remarks.append("Arrear Cleared!")

        total_deduction = ec + fc + duty + penalty + inst
        
        # Update Consumer
        consumer.wallet_balance -= total_deduction
        consumer.arrear_balance -= inst
        consumer.last_reading = current_kwh
        
        # Persist
        DataManager.add_ledger_entry(date_str, consumer.consumer_id, "Daily Bill", -total_deduction, "DEBIT")
        
        log_entry = {
            "Date": date_str, "Consumer ID": consumer.consumer_id, "Reading (KWh)": current_kwh,
            "Units Consumed": units_consumed, "EC (Energy)": round(ec, 2), "FC (Fixed)": round(fc, 2),
            "Duty": round(duty, 2), "Excess MD Charge": round(penalty, 2), "Installment": round(inst, 2),
            "Total Charges": round(total_deduction, 2), "Wallet Balance": round(consumer.wallet_balance, 2),
            "Remarks": ", ".join(remarks) if remarks else "-"
        }
        DataManager.add_reading_log(log_entry)
        DataManager.save_consumer(consumer)
        return log_entry

class MonthlySettlementEngine:
    """
    Implements the Production-Grade Logic:
    1. Identify Eligible Consumers (Active)
    2. Fetch Meter Data (First & Last Reading of Month)
    3. Calculate Monthly Charges (Shadow Bill)
    4. Wallet Adjustment (True-Up vs Daily)
    5. Sync & Close
    """
    @staticmethod
    def run_settlement(consumer, month_str, tariff):
        # Step 2: Fetch Meter Data (Simulated from logs)
        logs = st.session_state.readings
        # Filter logs for this consumer and month
        month_logs = [l for l in logs if l['Consumer ID'] == consumer.consumer_id and month_str in str(l['Date'])]
        
        if not month_logs:
            return {"status": "FAILED", "reason": "No reading data for this month"}
            
        # Sort by date
        month_logs.sort(key=lambda x: x['Date'])
        
        start_read = month_logs[0]['Reading (KWh)'] - month_logs[0]['Units Consumed'] # Infer start
        end_read = month_logs[-1]['Reading (KWh)']
        total_consumption = end_read - start_read
        
        # Step 3: Calculate Monthly Charges (Shadow Bill)
        # Apply Monthly Slab Logic (Example: 0-100 @ 3.0, >100 @ 5.0)
        energy_charge = 0
        if total_consumption <= 100:
            energy_charge = total_consumption * 3.0
        else:
            energy_charge = (100 * 3.0) + ((total_consumption - 100) * 5.0)
            
        fixed_charge = tariff['fixed_charge'] # Full Monthly FC
        duty = (energy_charge + fixed_charge) * tariff['duty_rate']
        
        # Sum of penalties/installments already captured in daily logs
        total_penalties = sum(l['Excess MD Charge'] for l in month_logs)
        total_installments = sum(l['Installment'] for l in month_logs)
        
        shadow_bill_amount = energy_charge + fixed_charge + duty + total_penalties + total_installments
        
        # Step 4: Wallet Adjustment (True-Up)
        # We compare Shadow Bill vs What was already deducted daily
        already_deducted = sum(l['Total Charges'] for l in month_logs)
        adjustment_needed = shadow_bill_amount - already_deducted
        
        settlement_status = "SUCCESS"
        
        # Apply Adjustment
        if adjustment_needed != 0:
            # Case A: Sufficient Balance (or tiny adjustment)
            if consumer.wallet_balance >= adjustment_needed:
                consumer.wallet_balance -= adjustment_needed
            # Case B: Insufficient Balance (Deficit Logic)
            else:
                deficit = adjustment_needed - consumer.wallet_balance
                consumer.wallet_balance = 0
                consumer.deficit_balance += deficit
                settlement_status = "DEFICIT"
                
            # Log the adjustment
            type_ = "DEBIT" if adjustment_needed > 0 else "CREDIT"
            DataManager.add_ledger_entry(
                datetime.now().strftime("%Y-%m-%d"), 
                consumer.consumer_id, 
                f"Monthly Settlement Adj ({month_str})", 
                -adjustment_needed, 
                type_
            )

        # Step 5: Snapshot & Close
        consumer.last_settlement_date = datetime.now().strftime("%Y-%m-%d")
        DataManager.save_consumer(consumer)
        
        result = {
            "month": month_str,
            "consumer_id": consumer.consumer_id,
            "consumption": total_consumption,
            "shadow_bill": round(shadow_bill_amount, 2),
            "already_deducted": round(already_deducted, 2),
            "adjustment": round(adjustment_needed, 2),
            "final_wallet": round(consumer.wallet_balance, 2),
            "deficit": round(consumer.deficit_balance, 2),
            "status": settlement_status
        }
        DataManager.add_settlement(result)
        return result

# ==========================================
# 3. STREAMLIT UI
# ==========================================

st.set_page_config(page_title="VoltEngine Enterprise", layout="wide", page_icon="⚡")
DataManager.init()

st.title("⚡ VoltEngine: Enterprise Billing")

# Sidebar
st.sidebar.header("Navigation")
active_consumers = list(st.session_state.consumers.keys())
selected_c_id = st.sidebar.selectbox("Select Consumer", options=["Select"] + active_consumers)

# Tabs
tabs = st.tabs([
    "🔄 Migration", 
    "👤 Profile", 
    "📟 Reading Entry", 
    "📊 Daily Charge (DCC)", 
    "📅 Monthly Settlement", 
    "💰 Recharge"
])

# --- TAB 1: MIGRATION ---
with tabs[0]:
    st.header("Legacy Migration Utility")
    col1, col2, col3 = st.columns(3)
    with col1:
        old_acc = st.text_input("Old Account No", "KNO-998877")
        name = st.text_input("Name", "Ramesh Kumar")
    with col2:
        old_arrear = st.number_input("Arrears (₹)", value=5000.0)
        sec_dep = st.number_input("Security Deposit (₹)", value=1500.0)
    with col3:
        load = st.number_input("Load (KW)", value=5.0)
        close_read = st.number_input("Closing Reading", value=1000.0)
        
    if st.button("Migrate to Prepaid"):
        c = MigrationEngine.migrate(old_acc, name, "Patna, Bihar", old_arrear, sec_dep, load, close_read)
        DataManager.save_consumer(c)
        st.success(f"Migrated! New ID: {c.consumer_id}")

# --- TAB 2: PROFILE ---
with tabs[1]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        st.header(f"Consumer: {c.name} ({c.consumer_id})")
        
        with st.container():
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Status:** :green[{c.status}]")
            c1.markdown(f"**Load:** {c.load_kw} KW")
            c2.markdown(f"**Last Read:** {c.last_reading} KWh")
            c2.markdown(f"**Daily Inst:** ₹{c.installment.get('daily',0)}")
            
            c3.metric("Wallet Balance", f"₹{c.wallet_balance:.2f}")
            if c.deficit_balance > 0:
                c3.error(f"Deficit: ₹{c.deficit_balance:.2f}")
            c3.markdown(f"**Arrears:** ₹{c.arrear_balance:.2f}")
    else:
        st.info("Select a consumer.")

# --- TAB 3: READING ---
with tabs[2]:
    st.header("Daily Reading Entry")
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        col1, col2 = st.columns(2)
        r_date = col1.date_input("Date", datetime.today())
        curr_read = col2.number_input("Current Reading", min_value=c.last_reading, value=c.last_reading + 10)
        max_md = col2.number_input("MD (KW)", value=4.0)
        
        if st.button("Calculate Daily Bill"):
            tariff = {"rate": 3.0, "fixed_charge": 120, "duty_rate": 0.05, "demand_rate": 250}
            engine = PrepaidDailyBilling()
            res = engine.run(c, curr_read, max_md, tariff, str(r_date))
            if "error" not in res: st.success("Deducted Successfully!")
    else:
        st.warning("Select Consumer")

# --- TAB 4: DCC ---
with tabs[3]:
    st.header("Daily Charge Sheet")
    if selected_c_id != "Select":
        c_logs = [l for l in st.session_state.readings if l['Consumer ID'] == selected_c_id]
        if c_logs:
            df = pd.DataFrame(c_logs)
            cols = ["Date", "Reading (KWh)", "EC (Energy)", "FC (Fixed)", "Total Charges", "Wallet Balance", "Remarks"]
            st.dataframe(df[cols], width="stretch")
        else:
            st.info("No Data")

# --- TAB 5: MONTHLY SETTLEMENT (NEW LOGIC) ---
with tabs[4]:
    st.header("Monthly Settlement & Sync")
    st.info("Reconciles Daily Deductions against Actual Monthly Bill (Shadow Bill).")
    
    if selected_c_id != "Select":
        col1, col2 = st.columns(2)
        month_sel = col1.selectbox("Select Month", ["2026-01", "2026-02", "2026-03"])
        
        if st.button("Run Settlement Batch"):
            c = DataManager.get_consumer(selected_c_id)
            tariff = {"fixed_charge": 120, "duty_rate": 0.05} # Base tariff
            
            result = MonthlySettlementEngine.run_settlement(c, month_sel, tariff)
            
            if result.get("status") == "FAILED":
                st.error(result["reason"])
            else:
                st.success("Settlement Completed Successfully!")
                
                # Visual Bill Representation
                st.subheader("🧾 Shadow Bill Summary")
                b1, b2, b3 = st.columns(3)
                b1.metric("Actual Bill Amount", f"₹{result['shadow_bill']}")
                b2.metric("Already Deducted", f"₹{result['already_deducted']}")
                b3.metric("Adjustment Applied", f"₹{result['adjustment']}", 
                          delta="Credit" if  result['adjustment'] < 0 else "Debit", delta_color="inverse")
                
                st.json(result)
        
        # Show Settlement History
        st.markdown("---")
        st.subheader("Settlement History")
        hist = [s for s in st.session_state.settlements if s['consumer_id'] == selected_c_id]
        if hist:
            st.dataframe(pd.DataFrame(hist), width="stretch")

# --- TAB 6: RECHARGE ---
with tabs[5]:
    st.header("Recharge")
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        amt = st.number_input("Amount", value=500.0)
        if st.button("Recharge"):
            c.wallet_balance += amt
            # Clear deficit first if exists
            if c.deficit_balance > 0:
                recov = min(c.wallet_balance, c.deficit_balance)
                c.wallet_balance -= recov
                c.deficit_balance -= recov
                st.warning(f"₹{recov} used to clear previous deficit.")
                
            DataManager.save_consumer(c)
            DataManager.add_ledger_entry(str(datetime.now().date()), c.consumer_id, "Recharge", amt, "CREDIT")
            st.success(f"New Balance: ₹{c.wallet_balance}")