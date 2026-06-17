import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import feedparser
import base64
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

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
        
search_query = st.text_input("🔍 Rechercher une entreprise (nom ou ticker)", "Nvda", key="main_search_query")

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

# Mémorise les données globales pendant 24 heure
@st.cache_data(ttl=86400)
def get_ticker_info(ticker_symbol):
    action = yf.Ticker(ticker_symbol)
    return action.info

# Mémorise l'historique YTD pendant 24 heure
@st.cache_data(ttl=86400)
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Ratios", 
            "💰 Rentabilité", 
            "📈 Prix juste", 
            "📋 Earnings", 
            "🧠 Actualités", 
            "⚖️ Comparateur",
            "📈 Graphique"
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


            st.title("📂 Rapports Financiers Officiels (SEC Filings)")
            st.write(f"Accédez directement aux documents officiels déposés par **{company_name} ({ticker})**.")

            try:
                # 1. Récupération des rapports via la fonction native de yfinance
                filings = action.sec_filings
                
                if filings and isinstance(filings, list):
                    # On cherche le document le plus récent qui soit un 10-K (Annuel) ou 10-Q (Trimestriel)
                    rapport_trouve = None
                    for f in filings:
                        type_doc = f.get("type", "").upper()
                        if type_doc in ["10-K", "10-Q"]:
                            rapport_trouve = f
                            break # On s'arrête au premier trouvé car classés du plus récent au plus ancien
                    
                    if rapport_trouve:
                        type_doc = rapport_trouve.get("type")
                        date_publication = rapport_trouve.get("epochDate")
                        url_document = rapport_trouve.get("url")
                        
                        # Formatage de la date
                        date_texte = ""
                        if date_publication:
                            from datetime import datetime
                            date_texte = f"publié le {datetime.fromtimestamp(date_publication).strftime('%d/%m/%Y')}"

                        st.success(f"✅ Dernier rapport officiel **{type_doc}** trouvé ({date_texte}).")
                        
                        # 2. Le bouton cliquable
                        st.link_button(
                            label=f"🚀 Ouvrir le rapport {type_doc} officiel (PDF / HTML)",
                            url=url_document,
                            use_container_width=True,
                            help="Cliquez pour consulter le document original sur le site de la SEC."
                        )
                        
                    else:
                        st.info("💡 Aucun rapport récent de type 10-K ou 10-Q n'a été trouvé pour ce ticker.")
                        st.link_button("🔍 Rechercher manuellement sur SEC EDGAR", f"https://www.sec.gov/edgar/browse/?CIK={ticker}")
                else:
                    st.warning("⚠️ Les rapports SEC ne sont pas disponibles directement pour cette entreprise (Fréquent pour les actions hors-USA).")
                    st.link_button("🌐 Visiter le site Relations Investisseurs", infos.get("website", "https://google.com"))
            
            except Exception as e:
                st.error(f"Impossible de récupérer les rapports financiers : {e}")
                

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

        # --- CONTENU DU TAB 6 : LE COMPARATEUR DYNAMIQUE ET INTUITIF ---
        with tab6:
            st.title("⚖️ Comparateur d'Entreprises")
            st.write(f"Comparez **{company_name} ({ticker})** avec les entreprises de votre choix (max 3 au total).")

            # Initialisation de la liste des tickers comparés dans la session Streamlit
            if "tickers_comparateurs" not in st.session_state:
                st.session_state.tickers_comparateurs = []

            # L'entreprise principale est toujours incluse par défaut, on calcule les places restantes
            # Max 3 au total = Ticker principal + 2 tickers ajoutés
            places_restantes = 2 - len(st.session_state.tickers_comparateurs)

            st.markdown("---")
            st.subheader("🔍 Ajouter une entreprise au comparateur")
            
            if places_restantes > 0:
                # Utilisation de la même logique de recherche textuelle qu'au début du script
                search_comp = st.text_input(
                    f"Rechercher par nom ou ticker (Il vous reste {places_restantes} emplacement(s)) :", 
                    value="", 
                    key="search_comp_input"
                )
                
                if search_comp:
                    try:
                        # On réutilise ta fonction de cache globale fetch_search_results
                        quotes_comp = fetch_search_results(search_comp)
                        if quotes_comp:
                            options_comp = [f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Sans nom'))}" for q in quotes_comp]
                            selected_comp = st.selectbox("Sélectionnez l'entreprise à ajouter :", options_comp, key="select_comp_box")
                            ticker_to_add = selected_comp.split(" - ")[0]
                            
                            # Bouton pour valider l'ajout
                            if st.button(f"➕ Ajouter {ticker_to_add} au tableau", key="btn_add_ticker"):
                                if ticker_to_add == ticker:
                                    st.warning("Cette entreprise est déjà l'entreprise principale affichée.")
                                elif ticker_to_add in st.session_state.tickers_comparateurs:
                                    st.warning("Cette entreprise est déjà dans votre liste de comparaison.")
                                else:
                                    st.session_state.tickers_comparateurs.append(ticker_to_add)
                                    st.rerun()
                        else:
                            st.warning(f"Aucun résultat pour '{search_comp}'")
                    except Exception as e:
                        st.error(f"Erreur de recherche : {e}")
            else:
                st.info("💡 Vous avez atteint la limite de 3 entreprises (l'entreprise principale + 2 comparaisons). Supprimez-en une pour en ajouter une nouvelle.")

            # Affichage et gestion de la liste des entreprises ajoutées
            if st.session_state.tickers_comparateurs:
                st.write("**Entreprises ajoutées pour la comparaison :**")
                for t_comp in st.session_state.tickers_comparateurs:
                    col_t_name, col_t_btn = st.columns([4, 1])
                    col_t_name.write(f"• **{t_comp}**")
                    if col_t_btn.button(f"❌ Retirer", key=f"remove_{t_comp}"):
                        st.session_state.tickers_comparateurs.remove(t_comp)
                        st.rerun()

            # --- CONSTITUTION ET AFFICHAGE DE LA MATRICE COMPARATIVE ---
            # La liste finale contient toujours le ticker principal en premier
            liste_finale_tickers = [ticker] + st.session_state.tickers_comparateurs

            if len(liste_finale_tickers) < 2:
                st.info("💡 Utilisez la barre de recherche ci-dessus pour ajouter au moins une entreprise à juxtaposer.")
            else:
                donnees_comparatives = {}

                with st.spinner("Extraction et alignement des données financières..."):
                    for t_name in liste_finale_tickers:
                        try:
                            # Utilisation de ton cache existant get_ticker_info
                            info_comp = get_ticker_info(t_name)
                            
                            if info_comp and ("currency" in info_comp or "currencySymbol" in info_comp):
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
                                    "Rendement Div.": f"{info_comp.get('dividendYield', 0):.2f}%" if info_comp.get('dividendYield') else "0.00%",
                                    "Debt/Equity": f"{info_comp.get('debtToEquity', 0):.2f}%" if info_comp.get('debtToEquity') else "N/A",
                                }
                            else:
                                st.error(f"Impossible de récupérer des données valides pour {t_name}")
                        except Exception as e:
                            st.error(f"Erreur sur le ticker {t_name} : {e}")

                if donnees_comparatives:
                    df_comparatif = pd.DataFrame(donnees_comparatives)
                    st.markdown("---")
                    st.subheader("📊 Matrice comparative complète")
                    st.dataframe(df_comparatif, use_container_width=True)
                    

    # --- CONTENU DU TAB 7 : GRAPHIQUE EN CHANDELIERS ---
        with tab7:
            st.title(f"📈 Graphique Historique : {company_name}")
            st.write(f"Analyse technique visuelle pour **{ticker}**.")

            # 1. Sélection de la période par l'utilisateur
            periode_choisie = st.selectbox(
                "Période du graphique :",
                options=["1 mois", "3 mois", "6 mois", "1 an", "2 ans", "5 ans"],
                index=3,  # "1 an" par défaut
                key="graph_period_selector"
            )

            # Correspondance pour Yahoo Finance
            mapping_periodes = {
                "1 mois": "1mo",
                "3 mois": "3mo",
                "6 mois": "6mo",
                "1 an": "1y",
                "2 ans": "2y",
                "5 ans": "5y"
            }
            yf_period = mapping_periodes[periode_choisie]

            try:
                # 2. Récupération des données historiques via l'objet 'action' existant
                df_history = action.history(period=yf_period)

                if not df_history.empty:
                    import plotly.graph_objects as go

                    # 3. Création du graphique en chandeliers (Syntaxe Plotly corrigée)
                    fig = go.Figure(data=[go.Candlestick(
                        x=df_history.index,
                        open=df_history['Open'],
                        high=df_history['High'],
                        low=df_history['Low'],
                        close=df_history['Close'],
                        name=ticker,
                        increasing=dict(line_color='#26a69a', fillcolor='#26a69a'), # Vert émeraude
                        decreasing=dict(line_color='#ef5350', fillcolor='#ef5350')  # Rouge boursier
                    )])

                    # 4. Design et personnalisation du Layout
                    fig.update_layout(
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=500, # Un peu plus grand vu qu'il est seul dans l'onglet
                        paper_bgcolor='#fffdf4',  # Fond de ton application
                        plot_bgcolor='white',     # Fond du graphique
                        xaxis_rangeslider_visible=True,  # Curseur de zoom en bas
                        xaxis=dict(
                            gridcolor='#f0f0f0',
                            tickfont=dict(color='black')
                        ),
                        yaxis=dict(
                            gridcolor='#f0f0f0',
                            side="right",  # Prix à droite style TradingView
                            tickfont=dict(color='black')
                        ),
                        hovermode="x unified"  # Tooltip vertical complet au survol
                    )

                    # 5. Affichage dans Streamlit
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.warning("Aucune donnée historique trouvée pour cette période.")
            except Exception as e:
                st.error(f"Erreur lors de la génération du graphique : {e}")

    except Exception as e:
        st.error(f"Erreur avec {ticker} : {e}")
