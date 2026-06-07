import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import subprocess

# Set page config for wide layout and premium title
st.set_page_config(
    page_title="Indian Programmatic Supply Chain Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS variables for dark/light adaptation
st.markdown("""
    <style>
    /* Main App Header styling */
    .app-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 25px;
        color: white;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2);
    }
    .app-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .app-header p {
        margin: 5px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* Subtle container borders */
    div[data-testid="stVerticalBlock"] > div {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "indian_adtech_supply_chain.csv"

def run_scraper():
    """Runs the verify_supply_chain.py scraper script to generate the CSV dataset."""
    try:
        # Run scraping script synchronously
        result = subprocess.run(["python", "verify_supply_chain.py"], capture_output=True, text=True, check=True)
        return True, result.stdout
    except Exception as e:
        return False, str(e)

# --- Sidebar Configuration ---
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=80)
st.sidebar.title("Supply Chain Control")
st.sidebar.markdown("""
Verify authorized digital sellers (ads.txt) against global SSP listings (sellers.json) for the Indian publishing market.
""")
st.sidebar.markdown("---")

# Error handling: check if the CSV file exists
if not os.path.exists(CSV_FILE):
    st.error(f"⚠️ Dataset '{CSV_FILE}' is missing.")
    st.info("The verification dataset needs to be scraped and compiled. You can trigger the scraper directly using the button below.")
    
    if st.button("🚀 Run Scraper & Verify Supply Chains"):
        with st.spinner("Scraping ads.txt & parsing sellers.json (this may take 30-45 seconds due to Google's 100MB sellers.json)..."):
            success, log_output = run_scraper()
            if success:
                st.success("✅ Supply chain verification completed successfully!")
                # Force refresh
                st.rerun()
            else:
                st.error("❌ Scraping failed. See error log below:")
                st.code(log_output)
    st.stop()

# --- Load Dataset ---
@st.cache_data
def load_data():
    return pd.read_csv(CSV_FILE)

df = load_data()

# --- Dual-Filter Engine ---
# interconnected logic: filtering publishers list or networks list.
# We populate the publisher dropdown first.
pub_options = ["All Publishers"] + sorted(list(df["publisher_domain"].unique()))
selected_pub = st.sidebar.selectbox("Select Indian Publisher", pub_options, index=0)

# Filter df by publisher to get corresponding networks (ensures no empty states)
if selected_pub != "All Publishers":
    df_for_net = df[df["publisher_domain"] == selected_pub]
else:
    df_for_net = df

net_options = ["All Networks"] + sorted(list(df_for_net["ssp_domain"].unique()))
selected_net = st.sidebar.selectbox("Select Ad Tech Network", net_options, index=0)

# Apply both filters to the final dataset
df_filtered = df.copy()
if selected_pub != "All Publishers":
    df_filtered = df_filtered[df_filtered["publisher_domain"] == selected_pub]
if selected_net != "All Networks":
    df_filtered = df_filtered[df_filtered["ssp_domain"] == selected_net]

# --- Main Dashboard Header ---
st.markdown("""
    <div class="app-header">
        <h1>Programmatic Supply Chain Auditor 🇮🇳</h1>
        <p>Cross-referencing publisher ads.txt configurations against SSP sellers.json entities for transparency verification.</p>
    </div>
""", unsafe_allow_html=True)

# --- Executive KPI Cards ---
total_paths = len(df_filtered)
direct_paths = len(df_filtered[df_filtered["relationship"] == "DIRECT"])
reseller_paths = len(df_filtered[df_filtered["relationship"] == "RESELLER"])

# Helper function to render a premium metric card
def render_kpi_card(label, value, color):
    st.markdown(
        f"""
        <div style="
            background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.05));
            border: 1px solid rgba(128, 128, 128, 0.15);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.03);
            margin-bottom: 20px;
        ">
            <span style="font-size: 13px; font-weight: 600; color: var(--text-color, #8c92ac); text-transform: uppercase; letter-spacing: 1px;">{label}</span>
            <h2 style="margin: 10px 0 0 0; font-size: 40px; font-weight: 800; color: {color};">{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

col1, col2, col3 = st.columns(3)
with col1:
    render_kpi_card("Total Supply Paths Verified", f"{total_paths:,}", "#3B82F6")
with col2:
    render_kpi_card("Direct Authorized Sellers", f"{direct_paths:,}", "#10B981")
with col3:
    render_kpi_card("Reseller Intermediaries", f"{reseller_paths:,}", "#F59E0B")

st.markdown("<br>", unsafe_allow_html=True)

# --- Side-by-Side Visualizations ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("### Top Ad Networks")
    # Top 10 Ad Networks horizontal bar chart
    ssp_counts = df_filtered["ssp_domain"].value_counts().reset_index()
    ssp_counts.columns = ["Ad Network", "Paths"]
    top_ssps = ssp_counts.head(10).sort_values(by="Paths", ascending=True)
    
    if not top_ssps.empty:
        fig_bar = px.bar(
            top_ssps,
            x="Paths",
            y="Ad Network",
            orientation='h',
            labels={"Paths": "Supply Path Count", "Ad Network": "SSP Domain"},
            color="Paths",
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=350,
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )
        fig_bar.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.15)')
        fig_bar.update_yaxes(showgrid=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No network distribution data available for the selected filters.")

with chart_col2:
    st.markdown("### DIRECT vs. RESELLER Ratio")
    # DIRECT vs. RESELLER ratio donut chart
    rel_counts = df_filtered["relationship"].value_counts().reset_index()
    rel_counts.columns = ["Relationship", "Count"]
    
    if not rel_counts.empty:
        fig_pie = px.pie(
            rel_counts,
            names="Relationship",
            values="Count",
            hole=0.6,
            color="Relationship",
            color_discrete_map={"DIRECT": "#10B981", "RESELLER": "#F59E0B"}
        )
        fig_pie.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=350,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hoverinfo='label+value+percent'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No relationship breakdown available for the selected filters.")

st.markdown("<br>", unsafe_allow_html=True)

# --- Filtered Raw Data Ledger ---
st.markdown("### 📋 Supply Chain Data Ledger")
st.markdown("Use the columns' headers to search, filter, and sort the raw records dynamically. Shows legal entities compiled from SSP `sellers.json` records.")

# Rename columns for presentation
df_presentation = df_filtered.rename(columns={
    "publisher_domain": "Publisher Domain",
    "ssp_domain": "SSP/Exchange Domain",
    "seller_id": "Seller/Account ID",
    "relationship": "Supply Relationship",
    "verified_legal_entity": "Verified Legal Entity Name"
})

st.dataframe(
    df_presentation,
    use_container_width=True,
    column_order=["Publisher Domain", "SSP/Exchange Domain", "Seller/Account ID", "Supply Relationship", "Verified Legal Entity Name"],
    height=400
)

# Summary of mapping stats
st.markdown("---")
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.markdown("💡 **Dashboard Tip:** Select specific Indian publisher domains in the sidebar to review single-site supply chains. Select specific Networks (like `google.com`) to evaluate transparency across publishers.")
with col_info2:
    # Calculate stats about top 3 SSP mapping coverage
    top3_subset = df_filtered[df_filtered["ssp_domain"].isin(["google.com", "criteo.com", "rubiconproject.com", "magnite.com"])]
    if len(top3_subset) > 0:
        matched_count = len(top3_subset[~top3_subset["verified_legal_entity"].str.contains("Unlisted|Not Tracked", case=False, na=False)])
        match_rate = (matched_count / len(top3_subset)) * 100
        st.markdown(f"📈 **Sellers.json Match Rate:** **{match_rate:.1f}%** of IDs from Google, Criteo, and Magnite are successfully resolved to entity names in this selection.")
    else:
        st.markdown("📈 **Sellers.json Match Rate:** No records from Google/Criteo/Magnite found in this selection.")
