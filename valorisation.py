import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import feedparser
import base64
import pandas as pd
from datetime import datetime

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

# --- ENDPOINT PING ---
if "ping" in st.query_params:
    st.write("Pong! App is alive.")
    st.stop()

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

# Mémorisation des résultats de recherche pendant 24h
@st.cache_data(ttl=86400)
def fetch_search_results(query):
    try:
        search_results = yf.Search(query, max_results=5)
        return search_results.quotes
    except:
        return []

search_query = st.text_input("🔍 Rechercher une entreprise (nom ou ticker)", "Nvidia", key="main_search_query")

if search_query:
    try:
        quotes = fetch_search_results(search_query)
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

# Mémorise les données globales pendant 1 heure
@st.cache_data(ttl=3600)
def get_ticker_info(ticker_symbol):
    action = yf.Ticker(ticker_symbol)
    return action.info

# Mémorise l'historique YTD pendant 1 heure
@st.cache_data(ttl=3600)
def get_ticker_ytd(ticker_symbol):
    action = yf.Ticker(ticker_symbol)
    return action.history(period="ytd")

if ticker:
    try:
        infos = get_ticker_info(ticker)
        action = yf.Ticker(ticker)

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
            hist_ytd = get_ticker_ytd(ticker)
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

        # --- AFFICHAGE DU PRIX (After-Hours + Style Pro) ---
        regular_market_price = infos.get("regularMarketPrice")
        current_price = infos.get("currentPrice", prix)
        post_market_price = infos.get("postMarketPrice") or infos.get("afterHoursPrice")
        pre_market_price = infos.get("preMarketPrice")
        market_state = infos.get("marketState", "").upper()

        is_market_closed = market_state in ["POST", "PRE"] or (datetime.now().hour >= 22)

        if is_market_closed:
            if post_market_price:
                display_price = post_market_price
                price_label = "Prix After-Hours"
                price_change = ((display_price - prev_close) / prev_close) * 100
            elif pre_market_price:
                display_price = pre_market_price
                price_label = "Prix Pre-Market"
                price_change = ((display_price - prev_close) / prev_close) * 100
            else:
                display_price = current_price
                price_label = "Prix de clôture"
                price_change = 0
                change_text = "N/A"
        else:
            display_price = current_price
            price_label = "Prix actuel"
            price_change = day_change if isinstance(day_change, (int, float)) else 0
            change_text = day_text

        if 'change_text' not in locals():
            change_color = "green" if price_change >= 0 else "red"
            change_text = f"{price_change:+.2f}%" if price_change != 0 else "0%"
        else:
            change_color = "green" if (isinstance(price_change, (int, float)) and price_change >= 0) else "red"

        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #001f3f;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 14px; color: #666; font-weight: bold;">{price_label}</span>
                    <div style="font-size: 32px; font-weight: 700; color: black; margin-top: 5px;">
                        {display_price:.2f} {devise}
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 14px; color: {change_color}; font-weight: bold;">
                        {change_text}
                    </span>
                    <div style="font-size: 12px; color: #666; margin-top: 3px;">
                        {ytd_text}
                    </div>
                </div>
            </div>
        </div>
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
            
        # --- LOGIQUE DES ONGLETS MODIFIÉE POUR INCLURE LE TAB 6 ---
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🔢 Ratios", 
            "📊 Valorisation", 
            "💰 Prix d'entrée", 
            "🎙️ Calendrier & Dividendes", 
            "📰 Actualités",
            "⚖️ Comparateur"
        ])
        
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
                    st.write(f"**Debt/Equity** : {debt_to_equity:.2f}%")
                else:
                    st.write("**Debt/Equity** : N/A")

            with col2:
                try:
                    ocf_ttm = infos.get("operatingCashflow")
                    fcf_ttm = infos.get("freeCashflow")
                    if ocf_ttm and fcf_ttm:
                        capex_ttm = fcf_ttm - ocf_ttm
                    else:
                        cashflow = action.cashflow
                        capex_ttm = cashflow.loc["Capital Expenditure"].iloc[0]
                        ocf_ttm = cashflow.loc["Operating Cash Flow"].iloc[0]
                        fcf_ttm = cashflow.loc["Free Cash Flow"].iloc[0]

                    st.write(f"**CAPEX** : {format_valeur(abs(capex_ttm), devise)}")
                    st.write(f"**Op Cash Flow** : {format_valeur(ocf_ttm, devise)}")
                    if ocf_ttm and ocf_ttm != 0:
                        ratio_capex_ocf = abs(capex_ttm) / ocf_ttm * 100
                        st.write(f"**CAPEX/OCF** : {ratio_capex_ocf:.1f} %")
                    else:
                        st.write("**CAPEX/OCF** : N/A")

                    gross_margin = infos.get("grossMargins")
                    if gross_margin is not None:
                       st.write(f"**Gross Margin** : {gross_margin * 100:.1f} %")
                    else:
                       st.write("**Gross Margin** : N/A")
                       
                    profit_margin = infos.get("profitMargins")
                    if profit_margin is not None:
                        st.write(f"**Profit Margin** : {profit_margin * 100:.1f} %")
                    else:
                        st.write("**Profit Margin** : N/A")

                    st.write(f"**Free Cash Flow** : {format_valeur(fcf_ttm, devise)}")
                except:
                    st.write("**CAPEX** : N/A")
                    st.write("**Op Cash Flow** : N/A")
                    st.write("**CAPEX/OCF** : N/A")
                    st.write("**Free Cash Flow** : N/A")

            with col3:
                roe = infos.get("returnOnEquity")
                if roe is not None:
                    st.write(f"**ROE** : {roe * 100:.1f} %")
                else:
                    st.write("**ROE** : N/A")
                
                roic = infos.get("returnOnAssets")
                if roic is not None:
                    st.write(f"**ROA** : {roic * 100:.1f} %")
                else:
                    st.write("**ROA** : N/A")

                dividend_yield = infos.get("dividendYield")
                if dividend_yield is not None:
                    st.write(f"**Dividend Yield** : {dividend_yield:.2f} %")
                else:
                    st.write("**Dividend Yield** : N/A")

                price_to_book = infos.get("priceToBook")
                if price_to_book is not None:
                    st.write(f"**Price/Book** : {price_to_book:.2f}")
                else:
                    st.write("**Price/Book** : N/A")

                try:
                    total_debt = infos.get("totalDebt")
                    fcf_ttm = infos.get("freeCashflow") or action.cashflow.loc["Free Cash Flow"].iloc[0]
                    if fcf_ttm and total_debt and fcf_ttm > 0:
                        debt_to_fcf = total_debt / fcf_ttm
                        st.write(f"**Debt/FCF** : {debt_to_fcf:.2f} ans")
                    else:
                        st.write("**Debt/FCF** : N/A")
                except:
                    st.write("**Debt/FCF** : N/A")

                try:
                    bs = action.balance_sheet
                    keys_to_check = ["Ordinary Shares Number", "Share Issued", "Total Common Shares Outstanding"]
                    shares_series = None
                    for key in keys_to_check:
                        if key in bs.index:
                            shares_series = bs.loc[key]
                            break
                    if shares_series is not None and len(shares_series) >= 2:
                        shares_series = shares_series.dropna()
                        shares_recent = shares_series.iloc[0] 
                        shares_old = shares_series.iloc[-1]
                        if shares_old > 0:
                            shares_change = ((shares_recent - shares_old) / shares_old) * 100
                            emoji = "📈" if shares_change > 0 else "📉"
                            st.write(f"**Actions (évol.)** : {shares_change:+.1f} % {emoji}")
                        else:
                            st.write("**Actions (évol.)** : N/A")
                    else:
                        st.write("**Actions (évol.)** : N/A")
                except:
                    st.write("**Actions (évol.)** : N/A")

        with tab2:
            st.title("📊 Valorisation")
            horizon_m1 = st.number_input("Horizon d'investissement (années)", min_value=1, max_value=30, value=5, step=1)
            cagr_eps = st.number_input("Mon CAGR estimé pour les EPS (en %)", min_value=-100.0, value=12.0)
            eps_actuel = infos.get("trailingEps", 0.01)
            eps_futur = eps_actuel * ((1 + cagr_eps / 100) ** horizon_m1)
            per_estime = st.number_input(f"PER que j'estime dans {horizon_m1} ans", min_value=5.0, value=20.0)
            prix_cible = eps_futur * per_estime
            st.write(f"**Prix cible dans {horizon_m1} ans** : {prix_cible:.2f} {devise}")
            if isinstance(prix, (float, int)) and prix_cible > 0 and prix > 0:
                cagr_prix = ((prix_cible / prix) ** (1/horizon_m1) - 1) * 100
                if cagr_prix >= 10:
                    st.success(f"**CAGR au prix actuel ({horizon_m1} ans)** : {cagr_prix:.1f} %")
                else:
                    st.error(f"**CAGR au prix actuel ({horizon_m1} ans)** : {cagr_prix:.1f} %")

        with tab3:
            st.title("💰 Prix d'entrée juste")
            
            cagr_eps_custom = st.number_input(
                "Croissance annuelle estimée de l'EPS (%)", 
                value=cagr_eps, 
                key="cagr_method3" 
            )
            
            rendement_attendu = st.number_input("Rendement annuel attendu (%)", value=10.0)
            horizon = st.number_input("Nombre d'années", value=5, step=1)
            per_futur = st.number_input("PER que j'estime à l'horizon", min_value=5.0, value=20.0)
            
            prix_futur = eps_actuel * ((1 + cagr_eps_custom / 100) ** horizon) * per_futur
            prix_entree = prix_futur / ((1 + rendement_attendu / 100) ** horizon)
            
            if isinstance(prix, (float, int)) and prix > 0 and prix_futur > 0:
                if prix_entree >= prix:
                    st.success(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
                    st.info(f"Le prix actuel ({prix:.2f} {devise}) constitue un bon point d'entrée selon tes hypothèses.")
                else:
                    st.error(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
                    st.warning(f"Le prix actuel ({prix:.2f} {devise}) est surrévalué selon tes hypothèses.")

        with tab4:
            st.title("🎙️ Calendrier & Dividendes")
            
            next_earn_ts = infos.get('earningsTimestamp') 
            div_date_ts = infos.get('dividendDate')       
            ex_div_ts = infos.get('exDividendDate')      
            
            def format_ts(ts):
                if ts:
                    return datetime.fromtimestamp(ts).strftime('%d/%m/%Y')
                return "N/A"

            st.subheader("📅 Dates à surveiller")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("Prochains Earnings", format_ts(next_earn_ts))
            with c2:
                st.metric("Détachement Div.", format_ts(ex_div_ts))
            with c3:
                st.metric("Versement Div.", format_ts(div_date_ts))

            st.divider()

            st.subheader("📊 Dernier Résultat vs Estimations")
            
            eps_actual_val = infos.get('trailingEps', 'N/A')
            
            col_s1, col_s2, col_s3 = st.columns(3)
            
            with col_s1:
                st.write("**EPS Réalisé (TTM)**")
                st.write(f"{eps_actual_val} {devise}")
            
            with col_s2:
                target = infos.get('targetMeanPrice', 'N/A')
                st.write("**Objectif Analystes**")
                st.write(f"{target} {devise}")
                
            with col_s3:
                reco = infos.get('recommendationKey', 'N/A').upper()
                st.write("**Avis Global**")
                st.write(f" {reco}")

            st.subheader("💰 Derniers Versements")
            divs = action.dividends
            if not divs.empty:
                df_divs = divs.to_frame() 
                df_divs = df_divs.sort_index(ascending=False).head(5) 
                df_divs.index = df_divs.index.strftime('%d/%m/%Y')
                df_divs.columns = ['Montant']
                st.table(df_divs)
            else:
                st.write("Cette entreprise ne verse pas de dividendes.")

            st.divider()

            st.subheader("🏢 Classification Métier & Insiders")

            sec_display = infos.get('sector', 'N/A')
            ind_display = infos.get('industry', 'N/A')

            if sec_display != 'N/A' or ind_display != 'N/A':
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #001f3f; margin-bottom: 20px;">
                        <p style="margin-bottom: 10px; color: black !important; font-size: 16px;"><strong>Secteur :</strong> {sec_display}</p>
                        <p style="margin: 0; color: black !important; font-size: 16px;"><strong>Industrie :</strong> {ind_display}</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("📋 Informations sectorielles non disponibles")

            try:
                insider_val = infos.get('heldPercentInsiders')
                if insider_val is not None and insider_val != 0:
                    if insider_val < 1:
                        insider_pct = insider_val * 100
                    elif insider_val > 100:
                        insider_pct = insider_val / 100
                    else:
                        insider_pct = insider_val
                    
                    st.metric("👤 Actions détenues par les Insiders", f"{insider_pct:.2f}%")
                else:
                    st.write("📊 Détention des insiders non communiquée.")
            except:
                st.write("📊 Données insiders indisponibles.")

            st.divider()

        with tab5:
            st.title(f"📰 Dernières actualités : {company_name}")
            try:
                rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    for entry in feed.entries[:10]:
                        with st.container():
                            st.subheader(entry.title)
                            st.markdown(
                                f'<a href="{entry.link}" target="_system" rel="noopener noreferrer">'
                                f'🔗 Lire l\'article complet</a>',
                                unsafe_allow_html=True
                            )
                            st.divider()
                else:
                    st.info(f"Aucune actualité trouvée.")
            except Exception as e:
                st.error(f"Erreur news : {e}")

        # --- CONTENU DU TAB 6 : LE COMPARATEUR MULTI-TICKERS ---
        with tab6:
            st.title("⚖️ Comparateur d'Entreprises")
            st.write(f"Comparez **{company_name} ({ticker})** avec d'autres entreprises du secteur.")

            # Par défaut, on initialise la liste avec l'action actuellement recherchée
            entreprises_choisies = st.multiselect(
                "Sélectionnez ou tapez les tickers à mettre en concurrence (max 3) :",
                options=[ticker, "AAPL", "MSFT", "GOOGL", "META", "NVDA", "TTE", "SAN.PA", "BNP.PA", "PYPL"],
                default=[ticker],
                max_selections=3,
                key="comparison_multiselect"
            )

            if len(entreprises_choisies) < 2:
                st.info("💡 Veuillez ajouter au moins une autre entreprise dans la liste ci-dessus pour lancer le tableau comparatif.")
            else:
                donnees_comparatives = {}

                with st.spinner("Juxtaposition des métriques financières..."):
                    for t_name in entreprises_choisies:
                        try:
                            # Récupération via ta fonction de cache existante
                            info_comp = get_ticker_info(t_name)
                            devise_comp = info_comp.get("currencySymbol") or info_comp.get("currency") or ""
                            
                            donnees_comparatives[t_name] = {
                                "Nom": info_comp.get("longName", "N/A"),
                                "Secteur": info_comp.get("sector", "N/A"),
                                "Prix Actuel": f"{info_comp.get('currentPrice', 0):.2f} {devise_comp}" if info_comp.get('currentPrice') else "N/A",
                                "Capitalisation": f"{info_comp.get('marketCap', 0) / 1e9:.2f} Mds {devise_comp}" if info_comp.get('marketCap') else "N/A",
                                "PER (Trailing)": round(info_comp.get("trailingPE"), 2) if isinstance(info_comp.get("trailingPE"), (int, float)) else "N/A",
                                "Forward PER": round(info_comp.get("forwardPE"), 2) if isinstance(info_comp.get("forwardPE"), (int, float)) else "N/A",
                                "PEG Ratio": info_comp.get("pegRatio", "N/A"),
                                "P/B Ratio": round(info_comp.get("priceToBook"), 2) if isinstance(info_comp.get("priceToBook"), (int, float)) else "N/A",
                                "Marge Brute": f"{info_comp.get('grossMargins', 0) * 100:.2f}%" if info_comp.get('grossMargins') else "N/A",
                                "Marge Bénéficiaire": f"{info_comp.get('profitMargins', 0) * 100:.2f}%" if info_comp.get('profitMargins') else "N/A",
                                "Rendement Div.": f"{info_comp.get('dividendYield', 0) * 100:.2f}%" if info_comp.get('dividendYield') else "0.00%",
                                "Debt/Equity": f"{info_comp.get('debtToEquity', 0):.2f}%" if info_comp.get('debtToEquity') else "N/A",
                            }
                        except Exception as e:
                            st.error(f"Erreur avec le ticker {t_name} : {e}")

                if donnees_comparatives:
                    df_comparatif = pd.DataFrame(donnees_comparatives)
                    st.subheader("📊 Matrice comparative")
                    st.dataframe(df_comparatif, use_container_width=True)
                    
                    # Graphique rapide
                    st.markdown("---")
                    st.subheader("📈 Comparatif Visuel : PER vs Forward PER")
                    
                    graph_data = []
                    for t_name, metrics in donnees_comparatives.items():
                        t_per = metrics["PER (Trailing)"]
                        t_fper = metrics["Forward PER"]
                        
                        graph_data.append({
                            "Entreprise": t_name,
                            "PER (Trailing)": t_per if isinstance(t_per, (int, float)) else 0,
                            "Forward PER": t_fper if isinstance(t_fper, (int, float)) else 0
                        })
                    
                    df_graph = pd.DataFrame(graph_data).set_index("Entreprise")
                    st.bar_chart(df_graph)

    except Exception as e:
        st.error(f"Erreur avec {ticker} : {e}")
