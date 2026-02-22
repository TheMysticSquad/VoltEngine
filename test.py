import streamlit as st
import pandas as pd
from datetime import datetime
import calendar

# Attempt to import FPDF for PDF Generation
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False
    FPDF = None
import tempfile
import os

# ==========================================
# 0. PDF GENERATOR UTILITY (FILE-BUFFER FIX)
# ==========================================
class PDFGenerator:
    @staticmethod
    def _draw_section_header(pdf, title):
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(32, 74, 135) # Dark Blue
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 8, f"  {title}", border=1, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)

    @staticmethod
    def _draw_row(pdf, col1, col2, col3="", col4="", is_bold=False, fill=False):
        pdf.set_font("Arial", 'B' if is_bold else '', 10)
        if fill: pdf.set_fill_color(240, 240, 240)
        
        if col3 == "" and col4 == "":
            pdf.cell(140, 7, f"  {col1}", border=1, fill=fill)
            pdf.cell(50, 7, f"{col2}  ", border=1, ln=True, align='R', fill=fill)
        else:
            pdf.cell(70, 7, f"  {col1}", border=1, fill=fill)
            pdf.cell(40, 7, f"{col2}  ", border=1, align='R', fill=fill)
            pdf.cell(40, 7, f"{col3}  ", border=1, align='R', fill=fill)
            pdf.cell(40, 7, f"{col4}  ", border=1, ln=True, align='R', fill=fill)

    @staticmethod
    def _get_clean_pdf_bytes(pdf):
        """Bulletproof method to extract PDF bytes without encoding corruption."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            
        try:
            # Let FPDF write to a physical file natively
            try:
                pdf.output(temp_path)
            except Exception:
                pdf.output(name=temp_path, dest='F')
                
            # Read the clean binary data
            with open(temp_path, "rb") as f:
                pdf_bytes = f.read()
                
            return pdf_bytes
            
        finally:
            # The 'finally' block GUARANTEES the file is deleted from the 
            # cloud server, even if the code crashes on the line above!
            if os.path.exists(temp_path):
                os.remove(temp_path)
    @staticmethod
    def generate_conversion_bill(consumer, details):
        if not HAS_FPDF: return b"FPDF not installed."
        pdf = FPDF()
        pdf.add_page()
        
        # --- HEADER ---
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(32, 74, 135)
        pdf.cell(0, 10, "VOLTENGINE DISCOM UTILITY", ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "POSTPAID TO PREPAID CONVERSION BILL", ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # --- CONSUMER DETAILS ---
        pdf.set_font("Arial", '', 10)
        pdf.cell(40, 7, "Consumer ID:", border=1)
        pdf.cell(150, 7, f" {consumer.consumer_id}", border=1, ln=True)
        pdf.cell(40, 7, "Consumer Name:", border=1)
        pdf.cell(150, 7, f" {consumer.name}", border=1, ln=True)
        pdf.cell(40, 7, "Address:", border=1)
        pdf.cell(150, 7, f" {consumer.address}", border=1, ln=True)
        pdf.cell(40, 7, "Category & Load:", border=1)
        pdf.cell(150, 7, f" {consumer.category_id} | {consumer.load_kw} KW", border=1, ln=True)
        pdf.cell(40, 7, "Migration Date:", border=1)
        pdf.cell(150, 7, f" {details['mig_date']}", border=1, ln=True)
        pdf.ln(5)
        
        # --- SECTION A: UNBILLED PERIOD ---
        PDFGenerator._draw_section_header(pdf, "A. UNBILLED PERIOD CALCULATION")
        PDFGenerator._draw_row(pdf, "Previous Billed Reading", details['prev_r'])
        PDFGenerator._draw_row(pdf, "Migration Day Reading", details['mig_r'], fill=True)
        PDFGenerator._draw_row(pdf, "Units for Unbilled Period", details['units'], is_bold=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(190, 7, "  Detail Breakdown:", border=1, ln=True, fill=True)
        
        for slab in details['slab_breakdown']:
            PDFGenerator._draw_row(pdf, f"   {slab['desc']}", f"Rs. {slab['charge']:.2f}")
            
        PDFGenerator._draw_row(pdf, "Gross Energy Charge:", f"Rs. {details['gross_ec']:.2f}", is_bold=True, fill=True)
        PDFGenerator._draw_row(pdf, "Less: Subsidy:", f"-Rs. {details['subsidy']:.2f}")
        PDFGenerator._draw_row(pdf, "Fixed Charges (Prorated):", f"Rs. {details['fc']:.2f}")
        PDFGenerator._draw_row(pdf, "Electricity Duty:", f"Rs. {details['duty']:.2f}")
        PDFGenerator._draw_row(pdf, "DPS (Delayed Payment Surcharge):", "Rs. 0.00")
        PDFGenerator._draw_row(pdf, "Total Unbilled Amount:", f"Rs. {details['total_unbilled']:.2f}", is_bold=True, fill=True)
        pdf.ln(5)

        # --- SECTION B: RECONCILIATION ---
        PDFGenerator._draw_section_header(pdf, "B. ACCOUNT RECONCILIATION")
        PDFGenerator._draw_row(pdf, "Old Arrear:", f"Rs. {details['old_arrear']:.2f}")
        PDFGenerator._draw_row(pdf, "Add: Unbilled Amount:", f"Rs. {details['total_unbilled']:.2f}")
        total_out = details['old_arrear'] + details['total_unbilled']
        PDFGenerator._draw_row(pdf, "Total Outstanding:", f"Rs. {total_out:.2f}", is_bold=True, fill=True)
        PDFGenerator._draw_row(pdf, "Less: Security Deposit:", f"-Rs. {details['sec_dep']:.2f}")
        
        # Highlighted final balances
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(32, 74, 135)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(140, 8, "  OPENING ARREAR (Prepaid):", border=1, fill=True)
        pdf.cell(50, 8, f"Rs. {consumer.arrear_balance:.2f}  ", border=1, ln=True, align='R', fill=True)
        pdf.cell(140, 8, "  OPENING WALLET BALANCE:", border=1, fill=True)
        pdf.cell(50, 8, f"Rs. {consumer.wallet_balance:.2f}  ", border=1, ln=True, align='R', fill=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "Remarks:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(190, 6, f"   * Recovery Days: {details['rec_days']} Days", ln=True)
        pdf.cell(190, 6, f"   * Installment Per Day: Rs. {consumer.installment.get('daily', 0):.2f}", ln=True)

        # Call the new clean bytes method
        return PDFGenerator._get_clean_pdf_bytes(pdf)

    @staticmethod
    def generate_settlement_bill(consumer, res):
        if not HAS_FPDF: return b"FPDF not installed."
        pdf = FPDF()
        pdf.add_page()
        
        # --- HEADER ---
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(32, 74, 135)
        pdf.cell(0, 10, "VOLTENGINE DISCOM", ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "MONTHLY PREPAID SETTLEMENT INVOICE", ln=True, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        # Metadata table
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 7, f" Billing Month : {res['month']}", border=1)
        pdf.cell(95, 7, f" Invoice Date : {datetime.now().strftime('%d-%m-%Y')}", border=1, ln=True)
        pdf.cell(95, 7, f" Consumer ID : {consumer.consumer_id}", border=1)
        pdf.cell(95, 7, f" Category : {consumer.category_id} | Load: {consumer.load_kw}KW", border=1, ln=True)
        pdf.ln(5)

        # --- SECTION A: ACTUAL MONTHLY CHARGES ---
        PDFGenerator._draw_section_header(pdf, "A. ACTUAL MONTHLY CHARGES (SHADOW BILL)")
        PDFGenerator._draw_row(pdf, "Total Units (KWh)", f"{res['units']} KWh", is_bold=True, fill=True)
        PDFGenerator._draw_row(pdf, "Gross Energy Charge", f"Rs. {res['gross_ec']:.2f}")
        PDFGenerator._draw_row(pdf, "Less: Govt Subsidy", f"-Rs. {res['subsidy']:.2f}")
        PDFGenerator._draw_row(pdf, "Net Energy Charge", f"Rs. {res['net_ec']:.2f}", is_bold=True)
        PDFGenerator._draw_row(pdf, "Electricity Duty", f"Rs. {res['duty']:.2f}")
        PDFGenerator._draw_row(pdf, "Fixed Charge", f"Rs. {res['fc']:.2f}")
        PDFGenerator._draw_row(pdf, "[A] TOTAL ACTUAL MONTHLY CHARGES", f"Rs. {res['shadow_bill']:.2f}", is_bold=True, fill=True)
        pdf.ln(5)

        # --- SECTION B: DAILY DEDUCTIONS ---
        PDFGenerator._draw_section_header(pdf, "B. DAILY PREPAID DEDUCTIONS (ALREADY PAID)")
        PDFGenerator._draw_row(pdf, "Total Daily Energy Deducted", f"Rs. {res['daily_energy']:.2f}")
        PDFGenerator._draw_row(pdf, "Total Daily Fixed Deducted", f"Rs. {res['daily_fc']:.2f}")
        PDFGenerator._draw_row(pdf, "Total Daily Duty Deducted", f"Rs. {res['daily_duty']:.2f}")
        PDFGenerator._draw_row(pdf, "[B] TOTAL ALREADY DEDUCTED", f"Rs. {res['daily_deducted']:.2f}", is_bold=True, fill=True)
        pdf.ln(5)

        # --- SECTION C: TRUE-UP ---
        PDFGenerator._draw_section_header(pdf, "C. TRUE-UP SETTLEMENT")
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(70, 7, "  Component", border=1, fill=True)
        pdf.cell(40, 7, "Actual (A)  ", border=1, align='R', fill=True)
        pdf.cell(40, 7, "Deducted (B)  ", border=1, align='R', fill=True)
        pdf.cell(40, 7, "Difference  ", border=1, ln=True, align='R', fill=True)
        
        PDFGenerator._draw_row(pdf, "Energy Charge", f"{res['net_ec']:.2f}", f"{res['daily_energy']:.2f}", f"{(res['net_ec'] - res['daily_energy']):.2f}")
        PDFGenerator._draw_row(pdf, "Fixed Charge", f"{res['fc']:.2f}", f"{res['daily_fc']:.2f}", f"{(res['fc'] - res['daily_fc']):.2f}")
        PDFGenerator._draw_row(pdf, "Duty", f"{res['duty']:.2f}", f"{res['daily_duty']:.2f}", f"{(res['duty'] - res['daily_duty']):.2f}")
        
        diff = res['shadow_bill'] - res['daily_deducted']
        pdf.set_font("Arial", 'B', 11)
        adj_text = f"DEBIT of Rs. {diff:.2f}" if diff > 0 else f"CREDIT of Rs. {abs(diff):.2f}" if diff < 0 else "NIL"
        pdf.cell(190, 8, f"  Net True-Up Adjustment: {adj_text} applied to wallet.", border=1, ln=True)
        pdf.ln(5)

        # --- SECTION D: LEDGER ---
        PDFGenerator._draw_section_header(pdf, "D. PREPAID FINANCIAL LEDGER")
        PDFGenerator._draw_row(pdf, "Closing Arrear Balance:", f"Rs. {consumer.arrear_balance:.2f}")
        PDFGenerator._draw_row(pdf, "Closing Wallet Balance:", f"Rs. {consumer.wallet_balance:.2f}", is_bold=True, fill=True)
        
        pdf.ln(8)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 5, "This is a system-generated settlement statement. Please maintain sufficient wallet balance availability.", ln=True, align='C')

        # Call the new clean bytes method
        return PDFGenerator._get_clean_pdf_bytes(pdf)
# ==========================================
# 1. DATA MANAGER
# ==========================================
class DataManager:
    @staticmethod
    def init():
        if 'categories' not in st.session_state:
            st.session_state.categories = {
                "DS-II": {
                    "cat_id": "DS-II", "name": "Domestic Rural", "fixed_charge": 120.0,
                    "demand_rate": 250.0, "subsidy_rate": 1.00, "duty_rate": 0.05,
                    "slabs": [{"Upto KWh": 50, "Rate (₹)": 3.10}, {"Upto KWh": 100, "Rate (₹)": 3.60}, {"Upto KWh": 999999, "Rate (₹)": 4.10}]
                },
                "NDS-I": { 
                    "cat_id": "NDS-I", "name": "Non-Domestic Urban", "fixed_charge": 250.0,
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
    def __init__(self, consumer_id, name, address, category_id, wallet, arrear, load, installment, initial_reading, billing_month):
        self.consumer_id = consumer_id
        self.name = name
        self.address = address
        self.category_id = category_id
        self.wallet_balance = float(wallet)
        self.arrear_balance = float(arrear)
        self.load_kw = float(load)
        self.installment = installment 
        self.last_reading = float(initial_reading)
        self.current_billing_month = billing_month 
        self.status = "ACTIVE"
        self.negative_days = 0 
        self.amendments = []

class PaymentEngine:
    @staticmethod
    def process_recharge(consumer, amount):
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
        paid_amount = min(amount, consumer.arrear_balance)
        consumer.arrear_balance -= paid_amount
        if consumer.arrear_balance > 0:
            consumer.installment = {"daily": round(consumer.arrear_balance / recovery_days, 2), "recovery_days": recovery_days}
        else:
            consumer.installment = {"daily": 0.0, "recovery_days": 0}
        DataManager.save_consumer(consumer)
        DataManager.add_ledger_entry(datetime.now().date(), consumer.consumer_id, f"Arrear Payment Received", 0.0, "INFO", consumer.wallet_balance)
        return paid_amount

class SlabEngine:
    @staticmethod
    def calculate_energy_charge_with_breakdown(units, slabs):
        sorted_slabs = sorted(slabs, key=lambda x: x['Upto KWh'])
        charge = 0.0
        remaining_units = units
        prev_limit = 0
        breakdown = []
        
        for slab in sorted_slabs:
            slab_size = slab['Upto KWh'] - prev_limit
            if remaining_units <= 0: break
            units_in_slab = min(remaining_units, slab_size)
            cost = units_in_slab * slab['Rate (₹)']
            charge += cost
            
            upper_label = "Above" if slab['Upto KWh'] > 90000 else f"{slab['Upto KWh']}"
            breakdown.append({
                "desc": f"{prev_limit+1}-{upper_label} Units @ Rs.{slab['Rate (₹)']}",
                "charge": cost
            })
            
            remaining_units -= units_in_slab
            prev_limit = slab['Upto KWh']
            
        return charge, breakdown

class MigrationEngine:
    @staticmethod
    def migrate(old_acc, name, address, category_id, old_arrear, security_dep, load, prev_r, mig_r, mig_date, recovery_days=365):
        unbilled_units = max(0, mig_r - prev_r)
        tariff = DataManager.get_tariff(category_id)
        
        # Calculate with breakdown for the PDF
        gross_ec, slab_breakdown = SlabEngine.calculate_energy_charge_with_breakdown(unbilled_units, tariff['slabs'])
        subsidy = unbilled_units * tariff.get('subsidy_rate', 0.0)
        net_ec = max(0, gross_ec - subsidy)
        
        # Assume 30 days proration for migration unbilled period simplistically
        fc = tariff['fixed_charge']
        duty = (net_ec + fc) * tariff['duty_rate']
        
        total_unbilled = net_ec + fc + duty
        total_debt = float(old_arrear) + total_unbilled
        
        net_balance = total_debt - float(security_dep)
        new_wallet = abs(net_balance) if net_balance < 0 else 0.0
        new_arrear = net_balance if net_balance > 0 else 0.0
        inst_amt = round(new_arrear / recovery_days, 2) if new_arrear > 0 else 0
        
        start_month = mig_date.strftime("%Y-%m")
        c = Consumer(f"PRE-{old_acc}", name, address, category_id, new_wallet, new_arrear, load, {"daily": inst_amt, "recovery_days": recovery_days}, mig_r, start_month)
        
        DataManager.add_ledger_entry(mig_date, c.consumer_id, f"Unbilled Conv. ({unbilled_units} units)", -total_unbilled, "INFO", new_wallet)
        if new_wallet > 0:
            DataManager.add_ledger_entry(mig_date, c.consumer_id, "Opening Balance (Sec Dep Adj)", new_wallet, "CREDIT", new_wallet)
        
        # Return dict of details specifically for PDF generation
        pdf_details = {
            "prev_r": prev_r, "mig_r": mig_r, "mig_date": str(mig_date), "units": unbilled_units,
            "slab_breakdown": slab_breakdown, "gross_ec": gross_ec, "subsidy": subsidy,
            "fc": fc, "duty": duty, "total_unbilled": total_unbilled, "old_arrear": old_arrear,
            "sec_dep": security_dep, "rec_days": recovery_days
        }
        
        return c, pdf_details

class PrepaidDailyBilling:
    def run(self, consumer, current_kwh, max_demand, date_val, is_meter_change=False, is_non_com=False):
        tariff = DataManager.get_tariff(consumer.category_id)
        if not tariff: return {"error": "Invalid Tariff Category"}

        date_str = str(date_val)
        dt = datetime.strptime(date_str, "%Y-%m-%d") if isinstance(date_val, str) else date_val
        read_month = dt.strftime("%Y-%m")
        
        if read_month < consumer.current_billing_month:
            return {"error": f"Locked: Cannot post readings to {read_month}. Month is already settled."}

        remarks = []
        days_in_month = calendar.monthrange(dt.year, dt.month)[1]
        
        if is_non_com:
            units_consumed, gross_ec, subsidy, net_ec, penalty = 0, 0.0, 0.0, 0.0, 0.0
            fc = tariff['fixed_charge'] / days_in_month
            duty = fc * tariff['duty_rate']
            remarks.append("Non-Com (Fixed Charge Only)")
            if not is_meter_change: current_kwh = consumer.last_reading
        else:
            units_consumed = current_kwh - consumer.last_reading
            if units_consumed < 0: return {"error": "Negative Consumption. Check reading."}
            
            base_rate = min(tariff['slabs'], key=lambda x: x['Rate (₹)'])['Rate (₹)']
            gross_ec = units_consumed * base_rate
            subsidy = units_consumed * tariff.get('subsidy_rate', 0.0)
            net_ec = max(0, gross_ec - subsidy)
            
            fc = tariff['fixed_charge'] / days_in_month
            duty = (net_ec + fc) * tariff['duty_rate']
            
            penalty = 0.0
            if max_demand > consumer.load_kw:
                excess = max_demand - consumer.load_kw
                penalty = excess * tariff['demand_rate'] * 1.5 / days_in_month
                remarks.append(f"Excess Load (+{excess}KW)")

        inst = 0.0
        if consumer.arrear_balance > 0:
            inst = min(consumer.installment.get('daily', 0), consumer.arrear_balance)
            if inst == consumer.arrear_balance: remarks.append("Arrear Cleared!")

        total_deduction = net_ec + fc + duty + penalty + inst
        
        consumer.wallet_balance -= total_deduction
        consumer.arrear_balance -= inst
        if not is_meter_change: consumer.last_reading = current_kwh
        
        # D&R Logic
        if consumer.wallet_balance < 0:
            consumer.negative_days += 1
            if consumer.negative_days == 1: remarks.append("SMS: 1st Negative Alert")
            elif consumer.negative_days == 2: remarks.append("SMS: 2nd Negative Alert")
            elif consumer.negative_days == 3: remarks.append("SMS: Pre-Disconnection Notice")
            elif consumer.negative_days == 4:
                consumer.status = "DISCONNECTED"
                remarks.append("ACTION: Power Disconnected")
                consumer.amendments.append({"Date": date_str, "Type": "Status", "Details": "ACTIVE -> DISCONNECTED"})
        
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
    def run_settlement(consumer):
        month_str = consumer.current_billing_month
        
        if any(s['month'] == month_str and s['consumer_id'] == consumer.consumer_id for s in st.session_state.settlements):
            return {"status": "FAILED", "reason": f"Settlement for {month_str} already posted."}

        tariff = DataManager.get_tariff(consumer.category_id)
        logs = [l for l in st.session_state.readings if l['Consumer ID'] == consumer.consumer_id and month_str in str(l['Date'])]
        
        total_units = sum(l['Units'] for l in logs) if logs else 0
        
        # Exact slab calculation
        gross_ec, _ = SlabEngine.calculate_energy_charge_with_breakdown(total_units, tariff['slabs'])
        total_subsidy = total_units * tariff.get('subsidy_rate', 0.0)
        net_ec = max(0, gross_ec - total_subsidy)
        
        fixed_charge = tariff['fixed_charge']
        duty = (net_ec + fixed_charge) * tariff['duty_rate']
        
        shadow_bill = net_ec + fixed_charge + duty
        
        # Granular sum of what was ALREADY deducted
        daily_energy = sum(l['Net EC'] for l in logs) if logs else 0
        daily_fc = sum(l['FC'] for l in logs) if logs else 0
        daily_duty = sum(l['Duty'] for l in logs) if logs else 0
        daily_deducted = daily_energy + daily_fc + daily_duty
        
        adjustment = shadow_bill - daily_deducted
        
        status = "SUCCESS"
        if adjustment != 0:
            consumer.wallet_balance -= adjustment
            status = "SUCCESS" if consumer.wallet_balance >= 0 else "DEFICIT"
            type_ = "DEBIT" if adjustment > 0 else "CREDIT"
            DataManager.add_ledger_entry(datetime.now().strftime("%Y-%m-%d"), consumer.consumer_id, 
                                         f"Monthly True-Up Adj ({month_str})", -adjustment, type_, consumer.wallet_balance)

        invoice_desc = f"📜 INVOICE POSTED: {month_str} | Units: {total_units} | Total Bill: ₹{round(shadow_bill,2)}"
        DataManager.add_ledger_entry(datetime.now().strftime("%Y-%m-%d"), consumer.consumer_id, invoice_desc, 0.0, "INVOICE", consumer.wallet_balance)

        # Advance Billing Cycle
        y, m = map(int, month_str.split('-'))
        m = 1 if m == 12 else m + 1
        y = y + 1 if m == 1 else y
        consumer.current_billing_month = f"{y:04d}-{m:02d}"

        DataManager.save_consumer(consumer)
        
        # Pass rich data for PDF
        res = {
            "month": month_str, "consumer_id": consumer.consumer_id, "units": total_units,
            "gross_ec": gross_ec, "subsidy": total_subsidy, "net_ec": net_ec, "fc": fixed_charge, "duty": duty,
            "shadow_bill": shadow_bill, 
            "daily_energy": daily_energy, "daily_fc": daily_fc, "daily_duty": daily_duty, "daily_deducted": daily_deducted,
            "adjustment": adjustment, "status": status, "next_billing_month": consumer.current_billing_month
        }
        st.session_state.settlements.append(res)
        return res

# ==========================================
# 3. STREAMLIT UI
# ==========================================
st.set_page_config(page_title="VoltEngine Pro", layout="wide", page_icon="⚡")
DataManager.init()

if not HAS_FPDF:
    st.sidebar.warning("⚠️ FPDF library missing. PDF downloads will not work. Run `pip install fpdf2` in your server.")

st.title("⚡ VoltEngine: Billing & Recovery Simulator")

active_consumers = list(st.session_state.consumers.keys())
selected_c_id = st.sidebar.selectbox("Active Consumer", ["Select"] + active_consumers)

tabs = st.tabs(["⚙️ Masters", "🔄 Migration", "👤 Profile", "🛠️ Services", "📟 Readings", "📊 DCC", "💰 Finance", "📅 Settlement"])

# --- TAB 1: CATEGORY ---
with tabs[0]:
    st.write("Active Tariff Categories")
    for key, val in st.session_state.categories.items():
        with st.expander(f"{val['name']} ({key})"): st.json(val)

# --- TAB 2: MIGRATION ---
with tabs[1]:
    c1, c2, c3, c4 = st.columns(4)
    acc = c1.text_input("Old Acc", "KNO-001")
    cat = c1.selectbox("Category", list(st.session_state.categories.keys()))
    arr = c2.number_input("Old Arrears", 3000.0)
    sec = c2.number_input("Security Dep", 1000.0)
    ld = c3.number_input("Load (KW)", 2.0)
    mig_date = c3.date_input("Migration Date")
    prev_r = c4.number_input("Prev Billed Reading", value=400.0)
    curr_r = c4.number_input("Reading on Migration Day", value=450.0)
    
    if st.button("Migrate to Prepaid"):
        c, pdf_details = MigrationEngine.migrate(acc, "John Doe", "Patna, Bihar", cat, arr, sec, ld, prev_r, curr_r, mig_date)
        DataManager.save_consumer(c)
        st.success(f"Migrated: {c.consumer_id}")
        
        # Generate and store the beautiful PDF
        st.session_state[f"pdf_{c.consumer_id}_mig"] = PDFGenerator.generate_conversion_bill(c, pdf_details)

    if f"pdf_PRE-{acc}_mig" in st.session_state and isinstance(st.session_state[f"pdf_PRE-{acc}_mig"], bytes):
        st.download_button("⬇️ Download Final Conversion Bill PDF", data=st.session_state[f"pdf_PRE-{acc}_mig"], 
                           file_name=f"Conversion_Bill_{acc}.pdf", mime="application/pdf")

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
        colC.markdown(f"**Active Month:** {c.current_billing_month}")
        colD.info(f"Installment: ₹{c.installment.get('daily', 0)}/day ({c.installment.get('recovery_days', 0)} days left)")
        
        if c.amendments:
            st.subheader("📝 Amendment History")
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
                    st.success("Updated!")
        with col2:
            st.subheader("2. Meter Replacement (MCO)")
            final_read = st.number_input("Final Reading of OLD Meter", min_value=c.last_reading, value=c.last_reading + 5)
            initial_read = st.number_input("Initial Reading of NEW Meter", value=0.0)
            mco_date = st.date_input("MCO Date")
            if st.button("Execute Meter Replacement"):
                res = PrepaidDailyBilling().run(c, final_read, c.load_kw, mco_date, is_meter_change=True)
                if "error" not in res:
                    c.last_reading = initial_read
                    c.amendments.append({"Date": str(mco_date), "Type": "Meter Replacement", "Details": f"Old Final: {final_read} | New Initial: {initial_read}"})
                    DataManager.save_consumer(c)
                    st.success("Meter Replaced!")

# --- TAB 5: READINGS ---
with tabs[4]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        st.info(f"Active billing month: **{c.current_billing_month}**")
        
        is_non_com = st.checkbox("⚠️ Mark as Non-Communicating (Non-Com)")
        
        col1, col2 = st.columns(2)
        r_date = col1.date_input("Date")
        
        if is_non_com:
            st.warning("Meter is marked Non-Com. Only Fixed Charge & Installments will be billed.")
            curr_read, max_md = c.last_reading, 0.0
        else:
            curr_read = col2.number_input("Reading", min_value=c.last_reading, value=c.last_reading + 8)
            max_md = col2.number_input("Max Demand", value=c.load_kw)
        
        if st.button("Run DCC"):
            res = PrepaidDailyBilling().run(c, curr_read, max_md, r_date, is_non_com=is_non_com)
            if "error" not in res: st.success("DCC Processed!")
            else: st.error(res["error"])

# --- TAB 6: DCC & LEDGER ---
with tabs[5]:
    if selected_c_id != "Select":
        dcc_tab, ledger_tab = st.tabs(["📊 DCC View", "📒 Ledger"])
        with dcc_tab:
            c_logs = [l for l in st.session_state.readings if l['Consumer ID'] == selected_c_id]
            if c_logs: st.dataframe(pd.DataFrame(c_logs), width="stretch")
        with ledger_tab:
            c_ledg = [l for l in st.session_state.ledger if l['Consumer ID'] == selected_c_id]
            if c_ledg:
                df_ledg = pd.DataFrame(c_ledg)
                def color_type(val):
                    color = 'green' if val == 'CREDIT' else 'red' if val == 'DEBIT' else 'blue' if val == 'INVOICE' else 'gray'
                    return f'color: {color}'
                st.dataframe(df_ledg.style.map(color_type, subset=['Type']), width="stretch")

# --- TAB 7: FINANCE ---
with tabs[6]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        pay_type = st.radio("Payment Type", ["Wallet Recharge", "Arrear Clearance"])
        if pay_type == "Wallet Recharge":
            w_amt = st.number_input("Recharge Amount (₹)", value=500.0)
            if st.button("Process Recharge"):
                PaymentEngine.process_recharge(c, w_amt)
                st.success("Recharged!")
        elif pay_type == "Arrear Clearance":
            a_amt = st.number_input("Payment Amount (₹)", max_value=c.arrear_balance, value=min(1000.0, c.arrear_balance))
            rec_days = st.slider("New Recovery Period (Days)", 30, 730, 365)
            if st.button("Process Arrear Payment"):
                PaymentEngine.process_arrear_payment(c, a_amt, rec_days)
                st.success("Arrear Processed.")

# --- TAB 8: SETTLEMENT ---
with tabs[7]:
    if selected_c_id != "Select":
        c = DataManager.get_consumer(selected_c_id)
        st.header("Monthly Settlement & Invoice Generator")
        
        st.info(f"Ready to invoice for active month: **{c.current_billing_month}**")
        
        if st.button(f"Generate Invoice for {c.current_billing_month}"):
            res = MonthlySettlementEngine.run_settlement(c)
            if res.get("status") == "FAILED":
                st.error(res["reason"])
            else:
                st.success("Invoice Generated!")
                st.json(res)
                
                # Create the Evolved Monthly Settlement PDF
                st.session_state[f"pdf_{c.consumer_id}_inv_{res['month']}"] = PDFGenerator.generate_settlement_bill(c, res)

        # Show Download Button
        settled_months = [s['month'] for s in st.session_state.settlements if s['consumer_id'] == selected_c_id]
        for m in settled_months:
            key = f"pdf_{c.consumer_id}_inv_{m}"
            if key in st.session_state and isinstance(st.session_state[key], bytes):
                st.download_button(f"⬇️ Download Invoice PDF ({m})", data=st.session_state[key], 
                                   file_name=f"Invoice_{selected_c_id}_{m}.pdf", mime="application/pdf")