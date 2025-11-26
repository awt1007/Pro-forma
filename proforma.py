import streamlit as st
import numpy as np

# ---------- Page config ----------
st.set_page_config(
    page_title="Dev Pro-Forma Playground",
    layout="wide",
)

st.title("🏗️ Real Estate Dev Pro-Forma Playground")
st.caption("Adjust the sliders to see how the deal vibes change in real time.")

# ---------- Sidebar / Inputs ----------
st.sidebar.header("Project Scale")
buildable_sf = st.sidebar.slider(
    "Buildable SF",
    min_value=1000,
    max_value=30000,
    value=2000,
    step=100,
)
units = st.sidebar.slider(
    "Number of Units (for display)",
    min_value=1,
    max_value=100,
    value=10,
    step=1,
)

st.sidebar.header("Costs & Financing")
land_cost = st.sidebar.number_input(
    "Land Cost ($)",
    min_value=0,
    max_value=1_000_000,
    value=500_000,
    step=10_000,
)
hard_cost_per_sf = st.sidebar.slider(
    "Hard Cost per SF ($/SF)",
    min_value=100,
    max_value=800,
    value=350,
    step=10,
)
soft_cost_pct = st.sidebar.slider(
    "Soft Costs (% of hard costs)",
    min_value=5.0,
    max_value=30.0,
    value=15.0,
    step=1.0,
)
contingency_pct = st.sidebar.slider(
    "Contingency (% of hard + soft)",
    min_value=0.0,
    max_value=15.0,
    value=7.5,
    step=0.5,
)
loan_to_cost = st.sidebar.slider(
    "Loan-to-Cost (LTC, %)",
    min_value=0.0,
    max_value=85.0,
    value=65.0,
    step=1.0,
)
interest_rate = st.sidebar.slider(
    "Construction Interest Rate (% — just for info)",
    min_value=0.0,
    max_value=15.0,
    value=7.0,
    step=0.25,
)

st.sidebar.header("Income & Operations (Stabilized)")
rent_per_sf_year = st.sidebar.slider(
    "Rent per SF per Year ($/SF/yr)",
    min_value=15,
    max_value=100,
    value=45,
    step=1,
)
stabilized_vacancy_pct = st.sidebar.slider(
    "Vacancy & Collection Loss (% of PGI)",
    min_value=0.0,
    max_value=15.0,
    value=5.0,
    step=0.5,
)
op_ex_pct = st.sidebar.slider(
    "Operating Expenses (% of EGI)",
    min_value=15.0,
    max_value=60.0,
    value=35.0,
    step=1.0,
)

st.sidebar.header("Exit Assumptions")
exit_cap_rate = st.sidebar.slider(
    "Exit Cap Rate (%)",
    min_value=3.0,
    max_value=10.0,
    value=5.0,
    step=0.25,
)
sale_cost_pct = st.sidebar.slider(
    "Disposition Costs (% of sale price)",
    min_value=0.0,
    max_value=5.0,
    value=1.0,
    step=0.25,
)
hold_period_years = st.sidebar.slider(
    "Hold Period (years, for IRR)",
    min_value=1,
    max_value=10,
    value=4,
    step=1,
)

# ---------- Core Calculations ----------

# Costs
hard_costs = buildable_sf * hard_cost_per_sf
soft_costs = hard_costs * (soft_cost_pct / 100.0)
contingency = (hard_costs + soft_costs) * (contingency_pct / 100.0)
total_project_cost = land_cost + hard_costs + soft_costs + contingency

# Financing
loan_amount = total_project_cost * (loan_to_cost / 100.0)
equity_required = total_project_cost - loan_amount

# Income (stabilized, annual)
pgi = buildable_sf * rent_per_sf_year   # Potential Gross Income
vacancy_loss = pgi * (stabilized_vacancy_pct / 100.0)
egi = pgi - vacancy_loss                # Effective Gross Income
op_ex = egi * (op_ex_pct / 100.0)
noi = egi - op_ex

# Exit
cap_rate_decimal = exit_cap_rate / 100.0 if exit_cap_rate > 0 else 0.0001
stabilized_value = noi / cap_rate_decimal
sale_costs = stabilized_value * (sale_cost_pct / 100.0)
net_sale_before_debt = stabilized_value - sale_costs

developer_profit_unlevered = net_sale_before_debt - total_project_cost
dev_margin_on_cost = (
    developer_profit_unlevered / total_project_cost
    if total_project_cost > 0 else 0
)

# Simple levered payoff assumption:
# Invest equity at t=0, receive net_sale_before_debt - loan_amount at exit
equity_exit_cash = net_sale_before_debt - loan_amount
equity_profit = equity_exit_cash - equity_required
equity_multiple = (
    (equity_exit_cash / equity_required)
    if equity_required > 0 else 0
)

def calc_irr(equity_out, equity_in, years):
    """
    Very simple IRR: one negative cash flow at t=0, one positive at t=years.
    """
    if equity_in <= 0 or equity_out <= 0 or years <= 0:
        return None
    # IRR = (equity_out / equity_in)^(1/years) - 1
    return (equity_out / equity_in) ** (1.0 / years) - 1.0

irr = calc_irr(equity_exit_cash, equity_required, hold_period_years)

# ---------- Layout: Metrics + Tables ----------

    st.subheader("### Project Scale")
    st.write(f"**Buildable SF:** {buildable_sf:,.0f}")
    st.write(f"**Units (display only):** {units}")
    st.write(f"**Rent:** ${rent_per_sf_year}/SF/yr")
    st.write(f"**Exit Cap:** {exit_cap_rate:.2f}%")
    st.write(f"**Hold Period:** {hold_period_years} years")

st.markdown("---")

col_top_left, col_top_right = st.columns([1.6, 1])

with col_top_left:
    st.subheader("Deal Snapshot")

    m1, m2, m3, m4 = st.columns([2, 2, 2, 2])
    m1.metric("Equity Required", f"${equity_required:,.0f}")
    m2.metric("Total Project Cost", f"${total_project_cost:,.0f}")
    m3.metric("Dev Margin on Cost", f"{dev_margin_on_cost*100:,.1f}%")
    m4.metric("Equity Multiple", f"{equity_multiple:,.2f}x")

    m5, m6, m7 = st.columns(3)
    m5.metric("Stabilized NOI (Year 1)", f"${noi:,.0f}")
    m6.metric("Stabilized Value", f"${stabilized_value:,.0f}")
    if irr is not None:
        m7.metric("Levered IRR", f"{irr*100:,.1f}%")
    else:
        m7.metric("Levered IRR", "N/A")

st.markdown("---")
st.subheader("Mini Pro-Forma (Stabilized Year)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Potential Gross Income (PGI)", f"${pgi:,.0f}")
col2.metric("Vacancy Loss", f"${vacancy_loss:,.0f}")
col3.metric("Effective Gross Income (EGI)", f"${egi:,.0f}")
col4.metric("Operating Expenses", f"${op_ex:,.0f}")

st.markdown("#### Cost Breakdown")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Land Cost", f"${land_cost:,.0f}")
c2.metric("Hard Costs", f"${hard_costs:,.0f}")
c3.metric("Soft Costs", f"${soft_costs:,.0f}")
c4.metric("Contingency", f"${contingency:,.0f}")

st.markdown("#### Capital Stack")
k1, k2 = st.columns(2)
k1.metric("Loan Amount", f"${loan_amount:,.0f}")
k2.metric("Equity", f"${equity_required:,.0f}")

st.markdown("#### Exit & Profit")
e1, e2, e3 = st.columns(3)
e1.metric("Net Sale Before Debt", f"${net_sale_before_debt:,.0f}")
e2.metric("Unlevered Developer Profit", f"${developer_profit_unlevered:,.0f}")
e3.metric("Equity Profit", f"${equity_profit:,.0f}")

st.caption(
    "This is a simplified toy model: no phased cash flows, no construction draw timing, "
    "no lease-up curve, etc. But it’s great for quick feasibility vibes."
)
