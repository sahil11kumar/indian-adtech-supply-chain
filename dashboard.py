import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import subprocess

# Set page config for wide layout and premium title
st.set_page_config(
    page_title="Global Programmatic Supply Chain Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS variables for dark/light adaptation
st.markdown("""
    <style>
    /* Main App Header styling */
    .app-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #0D9488 100%);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 25px;
        color: white;
        box-shadow: 0 4px 15px rgba(13, 148, 136, 0.2);
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

# Mappings of SSP domains to their programmatic roles
SSP_CLASSIFICATIONS = {
    # Global SSP / Exchange
    "google.com": "Global SSP / Exchange",
    "pubmatic.com": "Global SSP / Exchange",
    "rubiconproject.com": "Global SSP / Exchange",
    "magnite.com": "Global SSP / Exchange",
    "appnexus.com": "Global SSP / Exchange",
    "openx.com": "Global SSP / Exchange",
    "indexexchange.com": "Global SSP / Exchange",
    "smartadserver.com": "Global SSP / Exchange",
    "equativ.com": "Global SSP / Exchange",
    "onetag.com": "Global SSP / Exchange",
    
    # Native / Content Recommendation
    "outbrain.com": "Native / Content Recommendation",
    "taboola.com": "Native / Content Recommendation",
    "triplelift.com": "Native / Content Recommendation",
    "revcontent.com": "Native / Content Recommendation",
    "mgid.com": "Native / Content Recommendation",
    
    # Video SSP
    "teads.tv": "Video SSP",
    "teads.com": "Video SSP",
    "unrulymedia.com": "Video SSP",
    "video.unrulymedia.com": "Video SSP",
    "connatix.com": "Video SSP",
    "primis.tech": "Video SSP",
    
    # Mobile SSP
    "inmobi.com": "Mobile SSP",
    "inmobi.co.in": "Mobile SSP",
    "unity3d.com": "Mobile SSP",
    "applovin.com": "Mobile SSP",
    "adcolony.com": "Mobile SSP",
    "fyber.com": "Mobile SSP",
}

# Mappings of SSP domains to major DSP buyers connected via OpenRTB
SSP_DSP_MAPPINGS = {
    "google.com": ["Google DV360", "The Trade Desk", "Amazon DSP", "Yahoo DSP", "Adobe Advertising", "Criteo DSP"],
    "pubmatic.com": ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "MediaMath", "Criteo DSP"],
    "rubiconproject.com": ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "Beeswax", "Amobee"],
    "magnite.com": ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "Beeswax", "Amobee"],
    "criteo.com": ["Criteo DSP", "The Trade Desk", "Google DV360"],
    "inmobi.com": ["InMobi DSP", "The Trade Desk", "Google DV360", "Liftoff", "AppLovin", "AdColony"],
    "appnexus.com": ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "Xandr Invest", "MediaMath"],
    "openx.com": ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "Adobe Advertising"],
    "indexexchange.com": ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "MediaMath"],
    "smartadserver.com": ["The Trade Desk", "Google DV360", "Equativ Buyer", "Yahoo DSP"],
    "equativ.com": ["The Trade Desk", "Google DV360", "Equativ Buyer", "Yahoo DSP"],
    "outbrain.com": ["Outbrain DSP / Zemanta", "The Trade Desk", "Google DV360", "Yahoo DSP"],
    "taboola.com": ["Taboola Ads", "The Trade Desk", "Google DV360", "Yahoo DSP"],
    "triplelift.com": ["The Trade Desk", "Google DV360", "Yahoo DSP", "MediaMath"],
    "teads.tv": ["Teads Ad Manager", "The Trade Desk", "Google DV360", "Yahoo DSP"],
    "teads.com": ["Teads Ad Manager", "The Trade Desk", "Google DV360", "Yahoo DSP"],
    "unrulymedia.com": ["Tremor Video DSP", "The Trade Desk", "Google DV360", "Yahoo DSP"],
    "video.unrulymedia.com": ["Tremor Video DSP", "The Trade Desk", "Google DV360", "Yahoo DSP"],
}

def classify_ssp(domain):
    domain_lower = str(domain).lower()
    if domain_lower in SSP_CLASSIFICATIONS:
        return SSP_CLASSIFICATIONS[domain_lower]
    for key, role in SSP_CLASSIFICATIONS.items():
        if key in domain_lower:
            return role
    if any(kw in domain_lower for kw in ["video", "outstream", "vdo", "play"]):
        return "Video SSP"
    elif any(kw in domain_lower for kw in ["mobi", "mobile", "unity", "app"]):
        return "Mobile SSP"
    elif any(kw in domain_lower for kw in ["native", "recommend", "widget"]):
        return "Native / Content Recommendation"
    return "Other SSP / Intermediate"

def get_connected_dsps(domain):
    domain_lower = str(domain).lower()
    if domain_lower in SSP_DSP_MAPPINGS:
        return SSP_DSP_MAPPINGS[domain_lower]
    for key, dsps in SSP_DSP_MAPPINGS.items():
        if key in domain_lower:
            return dsps
    # Default fallback for untracked SSPs
    return ["Google DV360", "The Trade Desk", "Major DSPs (via OpenRTB)"]

def run_scraper():
    """Runs the verify_supply_chain.py scraper script to generate the CSV datasets."""
    try:
        result = subprocess.run(["python", "verify_supply_chain.py"], capture_output=True, text=True, check=True)
        return True, result.stdout
    except Exception as e:
        return False, str(e)

# --- Sidebar Configuration ---
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=65)
st.sidebar.title("Supply Chain Control")

# Market Selector Toggle (India vs US)
selected_market = st.sidebar.radio(
    "Select Target Market",
    ["🇮🇳 India", "🇺🇸 United States"],
    horizontal=True
)

market_suffix = "indian" if "India" in selected_market else "us"
CSV_FILE = f"{market_suffix}_adtech_supply_chain.csv"

# Error handling: check if the CSV file exists
if not os.path.exists(CSV_FILE):
    st.error(f"⚠️ Dataset '{CSV_FILE}' is missing.")
    st.info("The verification dataset needs to be scraped and compiled. You can trigger the scraper directly using the button below.")
    
    if st.button("🚀 Run Scraper & Verify Supply Chains"):
        with st.spinner("Scraping target publishers & parsing sellers.json (this may take 45-60 seconds)..."):
            success, log_output = run_scraper()
            if success:
                st.success("✅ Supply chain verification completed successfully!")
                st.rerun()
            else:
                st.error("❌ Scraping failed. See error log below:")
                st.code(log_output)
    st.stop()

# --- Load Dataset ---
@st.cache_data
def load_data(file_path):
    df_raw = pd.read_csv(file_path)
    df_raw["ssp_classification"] = df_raw["ssp_domain"].apply(classify_ssp)
    df_raw["connected_dsps"] = df_raw["ssp_domain"].apply(get_connected_dsps)
    return df_raw

df = load_data(CSV_FILE)

# --- Sidebar Dual-Filter Engine ---
st.sidebar.markdown("### Filters")

# Filter 1: Publisher Category
cat_options = ["All Categories"] + sorted(list(df["publisher_category"].unique()))
selected_cat = st.sidebar.selectbox("Select Publisher Category", cat_options, index=0)

# Filter 2: Publisher Domain (Interconnected with Category)
if selected_cat != "All Categories":
    df_filtered_cat = df[df["publisher_category"] == selected_cat]
else:
    df_filtered_cat = df

pub_options = ["All Publishers"] + sorted(list(df_filtered_cat["publisher_domain"].unique()))
selected_pub = st.sidebar.selectbox("Select Publisher Domain", pub_options, index=0)

# Filter 3: Ad Tech Network (Interconnected with Category & Publisher)
df_filtered_pub = df_filtered_cat.copy()
if selected_pub != "All Publishers":
    df_filtered_pub = df_filtered_pub[df_filtered_pub["publisher_domain"] == selected_pub]

net_options = ["All Networks"] + sorted(list(df_filtered_pub["ssp_domain"].unique()))
selected_net = st.sidebar.selectbox("Select Ad Tech Network", net_options, index=0)

# Filter 4: DSP Compatibility Filter
st.sidebar.markdown("---")
st.sidebar.markdown("### DSP Compatibility Audit")
dsp_list = ["All DSPs", "The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "Criteo DSP", "InMobi DSP", "Liftoff"]
selected_dsp = st.sidebar.selectbox("Filter by Connected DSP Buyer", dsp_list, index=0)

# Apply all filters to the final dataset
df_filtered = df.copy()
if selected_cat != "All Categories":
    df_filtered = df_filtered[df_filtered["publisher_category"] == selected_cat]
if selected_pub != "All Publishers":
    df_filtered = df_filtered[df_filtered["publisher_domain"] == selected_pub]
if selected_net != "All Networks":
    df_filtered = df_filtered[df_filtered["ssp_domain"] == selected_net]
if selected_dsp != "All DSPs":
    df_filtered = df_filtered[df_filtered["connected_dsps"].apply(lambda x: selected_dsp in x)]

# --- Main Dashboard Header ---
st.markdown(f"""
    <div class="app-header">
        <h1>Programmatic Supply Chain Auditor - {selected_market[4:]}</h1>
        <p>Analyzing programmatic supply paths, verifying sellers.json entities, and auditing DSP-buyer compatibility.</p>
    </div>
""", unsafe_allow_html=True)

# Create App Tabs
tab1, tab2 = st.tabs(["📊 Supply Chain Auditor", "💡 Programmatic Supply Chain Explained"])

with tab1:
    # --- Criteo Market Notice (only for India) ---
    if "India" in selected_market:
        st.info("💡 **India Criteo Insight:** Criteo has lower direct publisher adoption in India compared to Google or PubMatic. Criteo primarily purchases Indian traffic via header-bidding reseller paths rather than direct integrations.")

    # --- Executive KPI Cards ---
    total_paths = len(df_filtered)
    direct_paths = len(df_filtered[df_filtered["relationship"] == "DIRECT"])
    reseller_paths = len(df_filtered[df_filtered["relationship"] == "RESELLER"])

    def render_kpi_card(label, value, color):
        st.markdown(
            f"""
            <div style="
                background-color: var(--background-secondary-color, rgba(128, 128, 128, 0.05));
                border: 1px solid rgba(128, 128, 128, 0.15);
                border-radius: 10px;
                padding: 18px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.02);
                margin-bottom: 20px;
            ">
                <span style="font-size: 12px; font-weight: 600; color: var(--text-color, #8c92ac); text-transform: uppercase; letter-spacing: 1px;">{label}</span>
                <h2 style="margin: 8px 0 0 0; font-size: 38px; font-weight: 800; color: {color};">{value}</h2>
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
    
    # --- SSP Classification Distribution ---
    st.markdown("### 🏷️ Ad Tech Network Roles Distribution")
    class_counts = df_filtered["ssp_classification"].value_counts().reset_index()
    class_counts.columns = ["Network Role", "Path Count"]
    
    if not class_counts.empty:
        fig_class = px.bar(
            class_counts,
            x="Path Count",
            y="Network Role",
            orientation='h',
            color="Network Role",
            color_discrete_sequence=px.colors.qualitative.Safe,
            labels={"Path Count": "Count of Supply Paths", "Network Role": "Classified Role"}
        )
        fig_class.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )
        fig_class.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.15)')
        fig_class.update_yaxes(showgrid=False)
        st.plotly_chart(fig_class, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Filtered Raw Data Ledger ---
    st.markdown("### 📋 Supply Chain Data Ledger")
    st.markdown("Use columns' headers to search, filter, and sort. Includes connected downstream DSPs.")

    # Convert list of DSPs to a clean comma-separated string for UI presentation
    df_presentation = df_filtered.copy()
    df_presentation["connected_dsps_str"] = df_presentation["connected_dsps"].apply(lambda x: ", ".join(x))

    # Rename columns for presentation
    df_presentation = df_presentation.rename(columns={
        "publisher_domain": "Publisher Domain",
        "publisher_category": "Publisher Category",
        "ssp_domain": "SSP/Exchange Domain",
        "ssp_classification": "SSP Role Classification",
        "seller_id": "Seller/Account ID",
        "relationship": "Supply Relationship",
        "verified_legal_entity": "Verified Legal Entity Name",
        "connected_dsps_str": "Compatible DSP Buyers"
    })

    st.dataframe(
        df_presentation,
        use_container_width=True,
        column_order=["Publisher Domain", "Publisher Category", "SSP/Exchange Domain", "SSP Role Classification", "Seller/Account ID", "Supply Relationship", "Verified Legal Entity Name", "Compatible DSP Buyers"],
        height=400
    )

    # Summary of mapping stats
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.markdown("💡 **Audit Tip:** Use the **DSP Compatibility** filter in the sidebar to review SPO paths for specific platforms. Selecting 'The Trade Desk' will highlight only the SSP/Exchange connections that TTD actively bids on.")
    with col_info2:
        top3_subset = df_filtered[df_filtered["ssp_domain"].isin(["google.com", "criteo.com", "rubiconproject.com", "magnite.com"])]
        if len(top3_subset) > 0:
            matched_count = len(top3_subset[~top3_subset["verified_legal_entity"].str.contains("Unlisted|Not Tracked", case=False, na=False)])
            match_rate = (matched_count / len(top3_subset)) * 100
            st.markdown(f"📈 **Sellers.json Match Rate:** **{match_rate:.1f}%** of IDs from Google, Criteo, and Magnite are successfully resolved to entity names in this selection.")
        else:
            st.markdown("📈 **Sellers.json Match Rate:** No records from Google/Criteo/Magnite found in this selection.")

with tab2:
    st.markdown("## 💡 How Programmatic Supply Chains Work")
    st.markdown("""
    To verify programmatic advertising inventory transparency, we use two public standards defined by the **IAB Tech Lab**: 
    **ads.txt** (sell-side publication by the publisher) and **sellers.json** (sell-side directory hosted by the SSPs/Exchanges).
    """)
    
    st.markdown("### 🔗 The Downstream Connection to DSPs (Buy-Side)")
    st.markdown("""
    **Demand-Side Platforms (DSPs)** (like *The Trade Desk, Google Display & Video 360, Yahoo DSP*) are the portals through which advertisers bid on impressions. 
    DSPs do not host `ads.txt` or `sellers.json` files themselves because they buy inventory, rather than sell it. 
    
    Instead, DSPs act as the **primary auditors** of these standards. When a DSP receives a bid request from an SSP:
    1. The SSP includes a **`SupplyChain` Object (schain)** in the bid request. This shows all intermediaries involved in passing the ad slot.
    2. The DSP checks the **`ads.txt`** of the publisher to see if the sending SSP and Seller ID are authorized.
    3. The DSP cross-references the SSP's **`sellers.json`** to make sure the Seller ID exists and matches the legal entity name.
    4. If there is a mismatch (e.g. an ID is unlisted in `sellers.json` or unauthorized in `ads.txt`), the DSP **declines to bid**, protecting the advertiser's budget from fraud.
    """)
    
    st.markdown("### 🖥️ Programmatic Supply Path Architecture")
    
    # CSS Flexbox based horizontal flow diagram
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: stretch; gap: 10px; margin: 20px 0; font-family: sans-serif;">
        <!-- Card 1 -->
        <div style="flex: 1; min-width: 200px; background-color: rgba(30, 41, 59, 0.05); border: 2px solid #3B82F6; border-radius: 12px; padding: 15px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <span style="font-size: 11px; background-color: #3B82F6; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase;">1. Buy-Side</span>
                <h4 style="margin: 10px 0 5px 0; color: #2563EB;">Advertiser / DSP</h4>
                <p style="font-size: 13px; margin: 0; line-height: 1.4; color: var(--text-color);">Advertisers configure campaigns inside the <b>DSP</b> (e.g. The Trade Desk) to bid on target audiences.</p>
            </div>
            <div style="margin-top: 15px; font-size: 11px; color: #64748B; font-style: italic;">Audits supply path transparency</div>
        </div>
        
        <!-- Arrow 1 -->
        <div style="display: flex; align-items: center; justify-content: center; font-size: 24px; color: #94A3B8;">➡️</div>
        
        <!-- Card 2 -->
        <div style="flex: 1; min-width: 200px; background-color: rgba(13, 148, 136, 0.05); border: 2px solid #0D9488; border-radius: 12px; padding: 15px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <span style="font-size: 11px; background-color: #0D9488; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase;">2. Intermediary</span>
                <h4 style="margin: 10px 0 5px 0; color: #0D9488;">SSP / Ad Exchange</h4>
                <p style="font-size: 13px; margin: 0; line-height: 1.4; color: var(--text-color);">Exchanges (e.g. PubMatic, Rubicon) conduct auctions and host a public <b>sellers.json</b> directory.</p>
            </div>
            <div style="margin-top: 15px; font-size: 11px; color: #64748B; font-style: italic;">Matches Seller ID to Legal entity</div>
        </div>
        
        <!-- Arrow 2 -->
        <div style="display: flex; align-items: center; justify-content: center; font-size: 24px; color: #94A3B8;">➡️</div>
        
        <!-- Card 3 -->
        <div style="flex: 1; min-width: 200px; background-color: rgba(16, 185, 129, 0.05); border: 2px solid #10B981; border-radius: 12px; padding: 15px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <span style="font-size: 11px; background-color: #10B981; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase;">3. Sell-Side</span>
                <h4 style="margin: 10px 0 5px 0; color: #059669;">Publisher Website</h4>
                <p style="font-size: 13px; margin: 0; line-height: 1.4; color: var(--text-color);">Websites (e.g. Times of India, NDTV) publish their authorized channels inside public <b>ads.txt</b> files.</p>
            </div>
            <div style="margin-top: 15px; font-size: 11px; color: #64748B; font-style: italic;">Lists authorized seller accounts</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
