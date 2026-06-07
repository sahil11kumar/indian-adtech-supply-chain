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

net_options = sorted(list(df_filtered_pub["ssp_domain"].unique()))
selected_nets = st.sidebar.multiselect("Select Ad Tech Networks (Searchable)", options=net_options, default=[])

# Filter 4: DSP Compatibility Filter
st.sidebar.markdown("---")
st.sidebar.markdown("### DSP Compatibility Audit")
dsp_options = ["The Trade Desk", "Google DV360", "Amazon DSP", "Yahoo DSP", "Criteo DSP", "InMobi DSP", "Liftoff"]
selected_dsps = st.sidebar.multiselect("Select Connected DSP Buyers (Searchable)", options=dsp_options, default=[])

# Filter 5: Relationship Filter
st.sidebar.markdown("---")
st.sidebar.markdown("### Supply Path Relationships")
selected_rels = st.sidebar.multiselect("Select Supply Relationships", options=["DIRECT", "RESELLER"], default=["DIRECT", "RESELLER"])

# Top X networks slider control
st.sidebar.markdown("---")
st.sidebar.markdown("### Visualization Controls")
top_x = st.sidebar.slider("Top Networks to Display", min_value=5, max_value=30, value=10, step=5)

# Apply all filters to the final dataset
df_filtered = df.copy()
if selected_cat != "All Categories":
    df_filtered = df_filtered[df_filtered["publisher_category"] == selected_cat]
if selected_pub != "All Publishers":
    df_filtered = df_filtered[df_filtered["publisher_domain"] == selected_pub]
if selected_nets:
    df_filtered = df_filtered[df_filtered["ssp_domain"].isin(selected_nets)]
if selected_dsps:
    df_filtered = df_filtered[df_filtered["connected_dsps"].apply(lambda x: any(dsp in x for dsp in selected_dsps))]
if selected_rels:
    df_filtered = df_filtered[df_filtered["relationship"].isin(selected_rels)]
else:
    df_filtered = df_filtered[df_filtered["relationship"].isin([])]

# --- Main Dashboard Header ---
clean_market = selected_market.split(" ", 1)[1] if " " in selected_market else selected_market
st.markdown(f"""
    <div class="app-header">
        <h1>Programmatic Supply Chain Auditor - {clean_market}</h1>
        <p>Analyzing programmatic supply paths, verifying sellers.json entities, and auditing DSP-buyer compatibility.</p>
    </div>
""", unsafe_allow_html=True)

# Create App Tabs
tab1, tab2 = st.tabs(["📊 Supply Chain Auditor", "💡 Programmatic Supply Chain Explained"])

with tab1:

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
        st.markdown(f"### Top {top_x} Ad Networks")
        ssp_counts = df_filtered["ssp_domain"].value_counts().reset_index()
        ssp_counts.columns = ["Ad Network", "Paths"]
        top_ssps = ssp_counts.head(top_x).sort_values(by="Paths", ascending=True)
        
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
            st.markdown(f"📈 **Sellers.json Match Rate:** **{match_rate:.1f}%** of IDs from top global SSPs are successfully resolved to entity names in this selection.")
        else:
            st.markdown("📈 **Sellers.json Match Rate:** No records from top global SSPs found in this selection.")

with tab2:
    st.markdown("""
<div style="font-family: 'Inter', -apple-system, sans-serif; color: var(--text-color, #E2E8F0);">
<div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(13, 148, 136, 0.15) 100%); border-left: 5px solid #0D9488; padding: 22px; border-radius: 8px; margin-bottom: 25px;">
<h3 style="margin-top: 0; color: #0D9488; font-size: 1.35rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">🛡️ The Foundation of Programmatic Transparency</h3>
<p style="margin: 6px 0 0 0; line-height: 1.6; font-size: 0.95rem; color: var(--text-color, #E2E8F0);">
Programmatic advertising utilizes automated real-time auctions to buy and sell ad impressions. To prevent fraud, domain spoofing, and hidden arbitrage fees, the industry relies on standard transparency protocols defined by the <b>IAB Tech Lab</b>.
</p>
</div>
<div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 30px;">
<div style="flex: 1; min-width: 280px; background-color: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
<span style="font-size: 24px;">📄</span>
<h4 style="margin: 0; color: #3B82F6; font-size: 1.15rem; font-weight: 700;">ads.txt</h4>
</div>
<p style="font-size: 0.88rem; line-height: 1.5; margin: 0; color: var(--text-color, #94A3B8); opacity: 0.95;">
<b>Authorized Digital Sellers (Sell-Side)</b><br>
A public text file hosted on the publisher's root domain (e.g., <i>publisher.com/ads.txt</i>). It declares exactly which ad exchanges/SSPs are authorized to sell the publisher's ad space, mapping them to specific account IDs.
</p>
</div>
<div style="flex: 1; min-width: 280px; background-color: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
<span style="font-size: 24px;">📇</span>
<h4 style="margin: 0; color: #10B981; font-size: 1.15rem; font-weight: 700;">sellers.json</h4>
</div>
<p style="font-size: 0.88rem; line-height: 1.5; margin: 0; color: var(--text-color, #94A3B8); opacity: 0.95;">
<b>SSP Seller Directory (Exchange-Side)</b><br>
A public JSON directory hosted by ad networks/SSPs (e.g., <i>ssp.com/sellers.json</i>). It maps account IDs back to the real legal entity name of the seller, identifying whether they are a <code>PUBLISHER</code> (direct) or an <code>INTERMEDIARY</code> (reseller).
</p>
</div>
<div style="flex: 1; min-width: 280px; background-color: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
<span style="font-size: 24px;">🔗</span>
<h4 style="margin: 0; color: #F59E0B; font-size: 1.15rem; font-weight: 700;">schain Object</h4>
</div>
<p style="font-size: 0.88rem; line-height: 1.5; margin: 0; color: var(--text-color, #94A3B8); opacity: 0.95;">
<b>SupplyChain Object (OpenRTB Protocol)</b><br>
A digital record passed in real-time within the bid request. It acts like a flight manifest, recording every intermediary node that touched the bid request from the publisher to the auction house, preventing spoofed hops.
</p>
</div>
</div>
<h3 style="color: var(--text-color, #F8FAFC); font-size: 1.25rem; font-weight: 700; margin-top: 30px; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">⚡ The Real-Time Auditing Flow</h3>
<p style="margin-top: 0; margin-bottom: 20px; font-size: 0.95rem; color: var(--text-color, #94A3B8); opacity: 0.9; line-height: 1.5;">
When an ad slot loads on a publisher's site, a Demand-Side Platform (DSP) must audit the supply path in under <b>100 milliseconds</b> before deciding to bid:
</p>
<div style="display: flex; flex-direction: column; gap: 14px; margin-bottom: 35px;">
<div style="display: flex; gap: 15px; background: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 10px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
<div style="background: #3B82F6; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; flex-shrink: 0;">1</div>
<div style="flex: 1;">
<h4 style="margin: 0 0 4px 0; color: var(--text-color, #F8FAFC); font-size: 0.98rem; font-weight: 700;">Bid Request Generation & schain Entry</h4>
<p style="margin: 0; font-size: 0.88rem; color: var(--text-color, #94A3B8); opacity: 0.9; line-height: 1.45;">
The publisher's webpage calls an SSP (e.g. PubMatic). The SSP constructs an OpenRTB bid request, logs its domain and member account ID inside the <code>schain</code> object, and sends it to demand buyers.
</p>
</div>
</div>
<div style="display: flex; gap: 15px; background: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 10px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
<div style="background: #10B981; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; flex-shrink: 0;">2</div>
<div style="flex: 1;">
<h4 style="margin: 0 0 4px 0; color: var(--text-color, #F8FAFC); font-size: 0.98rem; font-weight: 700;">Sell-Side Authorization Cross-Reference (ads.txt)</h4>
<p style="margin: 0; font-size: 0.88rem; color: var(--text-color, #94A3B8); opacity: 0.9; line-height: 1.45;">
The DSP (e.g. The Trade Desk) receives the request, fetches the publisher domain's <code>ads.txt</code> file, and verifies that the sending SSP's domain and the listed Seller ID are explicitly authorized.
</p>
</div>
</div>
<div style="display: flex; gap: 15px; background: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 10px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
<div style="background: #F59E0B; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; flex-shrink: 0;">3</div>
<div style="flex: 1;">
<h4 style="margin: 0 0 4px 0; color: var(--text-color, #F8FAFC); font-size: 0.98rem; font-weight: 700;">Legal Entity Authentication (sellers.json)</h4>
<p style="margin: 0; font-size: 0.88rem; color: var(--text-color, #94A3B8); opacity: 0.9; line-height: 1.45;">
The DSP checks the SSP's <code>sellers.json</code> directory. It resolves the Seller ID to its registered corporate name and audits whether the contract relationship (DIRECT vs. RESELLER) matches the declaration.
</p>
</div>
</div>
<div style="display: flex; gap: 15px; background: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 10px; padding: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
<div style="background: #EC4899; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem; flex-shrink: 0;">4</div>
<div style="flex: 1;">
<h4 style="margin: 0 0 4px 0; color: var(--text-color, #F8FAFC); font-size: 0.98rem; font-weight: 700;">Bidding Execution or Fraud Prevention Drop</h4>
<p style="margin: 0; font-size: 0.88rem; color: var(--text-color, #94A3B8); opacity: 0.9; line-height: 1.45;">
If all checks match, the DSP submits the brand's bid. If any mismatch occurs (e.g. ID missing in <code>sellers.json</code>, or unauthorized in <code>ads.txt</code>), the DSP drops the bid request immediately, blocking the bid.
</p>
</div>
</div>
</div>
<h3 style="color: var(--text-color, #F8FAFC); font-size: 1.25rem; font-weight: 700; margin-top: 30px; margin-bottom: 18px; display: flex; align-items: center; gap: 8px;">❓ Frequently Asked Questions</h3>
<div style="display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px;">
<div style="background-color: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 12px; padding: 20px;">
<h4 style="margin-top: 0; color: #3B82F6; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px;">Q: Why don't brand sites like Nike, Adidas, or Puma host ads.txt files?</h4>
<p style="margin: 0; font-size: 0.9rem; line-height: 1.6; color: var(--text-color, #94A3B8); opacity: 0.95;">
<b>Because they are buy-side advertisers, not sell-side publishers.</b><br>
An <code>ads.txt</code> file is designed to govern <i>sellers</i>. Storefronts like Nike, Adidas, Apple, or Puma do not sell third-party banner spaces on their product pages. They only buy inventory across news, entertainment, and sports sites to run their product ads. Since they have no digital ad inventory to sell, they have no reason to host an <code>ads.txt</code> file. Instead, their campaign managers set strict bid rules in their DSPs to only buy from verified publisher lines.
</p>
</div>
<div style="background-color: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 12px; padding: 20px;">
<h4 style="margin-top: 0; color: #3B82F6; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px;">Q: Why don't Demand-Side Platforms (DSPs) host ads.txt or sellers.json?</h4>
<p style="margin: 0; font-size: 0.9rem; line-height: 1.6; color: var(--text-color, #94A3B8); opacity: 0.95;">
<b>DSPs act as buyers and auditors.</b><br>
A DSP (like The Trade Desk) represents the buyer. Since a DSP does not route payouts to publishers or sell ad space, it has no sell-side directories. Instead, the DSP acts as the gatekeeper. It constantly crawls, processes, and stores the public <code>ads.txt</code> and <code>sellers.json</code> files hosted by publishers and SSPs worldwide to audit every bid request in real-time.
</p>
</div>
<div style="background-color: var(--secondary-background-color, #1E293B); border: 1px solid var(--border-color, #334155); border-radius: 12px; padding: 20px;">
<h4 style="margin-top: 0; color: #3B82F6; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px;">Q: What is the difference between a DIRECT and RESELLER relationship?</h4>
<p style="margin: 0; font-size: 0.9rem; line-height: 1.6; color: var(--text-color, #94A3B8); opacity: 0.95;">
<b>Direct contracts vs. Intermediary wrappers.</b><br>
- A <b>DIRECT</b> path indicates the SSP has a direct contract with the publisher and issues payouts directly to them.<br>
- A <b>RESELLER</b> path indicates the SSP pays a third-party intermediary network or wrapper that holds the direct contract with the publisher.<br>
Buyers prefer DIRECT paths because they eliminate extra tech-fee margins taken by intermediaries, ensuring maximum budget reaches the publisher.
</p>
</div>
</div>
</div>
""", unsafe_allow_html=True)
