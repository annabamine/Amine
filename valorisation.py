import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import feedparser
import base64

# 1. Toujours en premier
st.set_page_config(page_title="Value Quest", layout="centered")

# 2. Barre de titre (Logique Logo + HTML)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

logo_base64 = get_base64_image("logo.png")
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="nav-logo">'
else:
    logo_html = "🪙"

# Injection de la barre de navigation
st.markdown(f"""
    <style>
        header {{visibility: hidden !important;}}
        footer {{visibility: hidden !important;}}
        #MainMenu {{visibility: hidden !important;}}
        
        .block-container {{
            padding-top: 6rem !important; 
        }}

        .nav-bar {{
            background-color: #001f3f !important; 
            border-bottom: 3px solid #C0C0C0;
            padding: 12px;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.4);
        }}

        .nav-logo {{
            height: 35px;
            margin-right: 15px;
        }}
        
        .nav-title {{
            color: #FEF9ED !important; 
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-family: "Source Sans Pro", sans-serif; 
            margin: 0;
        }}
    </style>
    
    <div class="nav-bar">
        {logo_html}
        <span class="nav-title">VALUE QUEST</span>
    </div>
""", unsafe_allow_html=True)

# 3. Styles globaux
st.markdown("""
<style>
.stApp {
    background-color: #fffdf4;
}

.stMainBlockContainer *:not(.nav-bar):not(.nav-title) {
    color: black !important;
    font-size: 15px !important;
}

.stTabs [data-baseweb="tab"] p {
    color: black !important;
}

div[data-baseweb="select"] > div {
    background-color: white !important;
}
div[data-baseweb="popover"] ul {
    background-color: white !important;
}
div[data-baseweb="popover"] li {
    background-color: white !important;
    color: black !important;
}
div[data-baseweb="popover"] li:hover {
    background-color: #f0f0f0 !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div {
    color: black !important;
}

div.stNumberInput input, div.stTextInput input {
    background-color: white !important;
    color: black !important;
    border: 1px solid gray !important;
}

header, .stAppHeader {
    background-color: #fffdf4 !important;
}
</style>""", unsafe_allow_html=True)


search_query = st.text_input("🔍 Rechercher une entreprise (nom ou ticker)", "Apple")

if search_query:
    try:
        search_results = yf.Search(search_query, max_results=5)
        quotes = search_results.quotes
        if quotes:
            options = [f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Sans nom'))}" for q in quotes]
            selected = st.selectbox("Sélectionnez l'entreprise :", options)
            ticker = selected.split(" - ")[0]
        else:
            st.warning(f"Aucun résultat pour '{search_query}'")
            ticker = None
    except:
        ticker = search_query.upper()
else:
    ticker = None

if ticker:
    try:
        action = yf.Ticker(ticker)
        infos = action.info

        devise = infos.get("currencySymbol") or infos.get("currency") or ""
        prix = infos.get("currentPrice", 0)

        # --- CALCULS DE PERFORMANCE ---
        prev_close = infos.get("regularMarketPreviousClose")
        if isinstance(prix, (int, float)) and prev_close:
            day_change = ((prix - prev_close) / prev_close) * 100
            day_color = "green" if day_change >= 0 else "red"
            day_text = f"({day_change:+.2f}%)"
        else:
            day_text = ""
            day_color = "black"

        # Performance Year To Date (YTD)
        try:
            hist_ytd = action.history(period="ytd")
            if not hist_ytd.empty:
                price_jan_1st = hist_ytd['Close'].iloc[0]
                ytd_change = ((prix - price_jan_1st) / price_jan_1st) * 100
                ytd_text = f"{ytd_change:+.2f}% YTD"
            else:
                ytd_text = "N/A YTD"
        except:
            ytd_text = "N/A YTD"

        eps = infos.get("trailingEps", "Non dispo")
        per = infos.get("trailingPE", "Non dispo")
        fper = infos.get("forwardPE", "Non dispo")

        company_name = infos.get("longName", infos.get("shortName", "Inconnu"))
        st.write(f"**Entreprise** : {company_name}")
        
        website = infos.get("website", "")
        if website:
            domain = website.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            logo_url = f"https://logos-api.apistemic.com/domain:{domain}"
            try:
                st.image(logo_url, width=40)
            except:
                st.write("Logo non disponible")
        else:
            st.write("Pas de site web ou logo disponible")

        summary = infos.get("longBusinessSummary", "Résumé non disponible sur Yahoo")
        with st.expander("📄 Résumé de l'entreprise (Yahoo Finance)"):
            st.write(summary)

        # Affichage stylisé (Prix normal, Variations + Today en gras)
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 18px; color: black;">
                <span>
                    <strong>Prix actuel :</strong> {prix} {devise} 
                    <span style="color: {day_color}; margin-left: 10px; font-weight: bold;">
                        {day_text}
                    </span>
                </span>
                <span style="color: gray; font-size: 16px; font-weight: bold;">
                    {ytd_text}
                </span>
            </div>
            <hr style="margin-top: 5px; margin-bottom: 15px;">
        """, unsafe_allow_html=True)


        market_cap = infos.get("marketCap")
        if market_cap is not None:
            market_cap_billions = market_cap / 1_000_000_000
            st.write(f"**Market Cap** : {market_cap_billions:,.2f} Mds {devise}")
        else:
            st.write("**Market Cap** : N/A")

        def format_valeur(valeur, devise):
            if valeur is None or valeur == "N/A": return "N/A"
            abs_val = abs(valeur)
            if abs_val >= 1_000_000_000:
               return f"{valeur / 1_000_000_000:,.2f} Mds {devise}"
            else:
               return f"{valeur / 1_000_000:,.2f} M {devise}"
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔢 Ratios", "📊 Valorisation", "💰 Prix d'entrée", "🎙️ Calendrier & Dividendes", "📰 Actualités"])
        
        with tab1:
            st.title("🔢 Ratios financiers")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**PER (trailing)** : {per}")
                st.write(f"**PER (forward)** : {fper}")
                st.write(f"**EPS (trailing)** : {eps}")
                try:
                    ocf_ttm = infos.get("operatingCashflow")
                    if not ocf_ttm:
                        ocf_ttm = action.cashflow.loc["Operating Cash Flow"].iloc[0]
                    if ocf_ttm and market_cap and ocf_ttm > 0:
                        p_ocf = market_cap / ocf_ttm
                        st.write(f"**Price/OCF** : {p_ocf:.2f}")
                    else:
                        st.write("**Price/OCF** : N/A")
                except:
                    st.write("**Price/OCF** : N/A")

                try:
                    fcf_ttm = infos.get("freeCashflow")
                    if not fcf_ttm:
                        fcf_ttm = action.cashflow.loc["Free Cash Flow"].iloc[0]
                    if fcf_ttm and market_cap and fcf_ttm > 0:
                        price_to_fcf = market_cap / fcf_ttm
                        st.write(f"**Price/FCF** : {price_to_fcf:.2f}")
                    else:
                        st.write("**Price/FCF** : N/A")
                except:
                    st.write("**Price/FCF** : N/A")

                debt_to_equity = infos.get("debtToEquity")
                if debt_to_equity is not None:
                    st.write(f"