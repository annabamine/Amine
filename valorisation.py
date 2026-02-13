import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import feedparser
import base64
import requests

def get_fmp_earnings_data(ticker, api_key):
    # On force le ticker en majuscules
    ticker = ticker.upper()
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarter&limit=1&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]
            else:
                st.warning(f"FMP n'a pas de données trimestrielles pour {ticker}")
        elif response.status_code == 403:
            st.error("Clé API invalide ou quota dépassé (Erreur 403)")
        else:
            st.error(f"Erreur API FMP : {response.status_code}")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
    return None


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
            day_text = f"({day_change:+.2f}% Today)"
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


        # Affichage stylisé 
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
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔢 Ratios", "📊 Valorisation", "💰 Prix d'entrée", "📰 Actualités", "🎙️ Earnings"])
        
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
            rendement_attendu = st.number_input("Rendement annuel attendu (%)", value=10.0)
            horizon = st.number_input("Nombre d'années", value=5, step=1)
            per_futur = st.number_input("PER que j'estime à l'horizon", min_value=5.0, value=20.0)
            prix_futur = eps_actuel * ((1 + cagr_eps / 100) ** horizon) * per_futur
            prix_entree = prix_futur / ((1 + rendement_attendu / 100) ** horizon)
            if isinstance(prix, (float, int)) and prix > 0 and prix_futur > 0:
                if prix_entree >= prix:
                    st.success(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
                else:
                    st.error(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")

        with tab4:
            st.title(f"📰 Dernières actualités : {company_name}")
            try:
                rss_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    for entry in feed.entries[:10]:
                        with st.container():
                            st.subheader(entry.title)
                            st.link_button("Lire l'article complet", entry.link)
                            st.divider()
                else:
                    st.info(f"Aucune actualité trouvée.")
            except Exception as e:
                st.error(f"Erreur news : {e}")


        with tab5:
            st.title(f"🎙️ Résultats Trimestriels")
            
            # Ta clé bien entourée de guillemets
            fmp_key = "mmAvgD5gdIBcSLVP1tfPmvohVTFpyEQI" 
            
            if ticker:
                e_data = get_fmp_earnings_data(ticker, fmp_key)
                
                if e_data:
                    # On récupère les valeurs
                    periode = e_data.get('period', 'N/A')
                    annee = e_data.get('calendarYear', 'N/A')
                    date_publi = e_data.get('date', 'N/A')
                    rev = e_data.get('revenue', 0)
                    net = e_data.get('netIncome', 0)
                    
                    st.subheader(f"📊 Rapport {periode} {annee}")
                    st.markdown(f"📅 Publié le : **{date_publi}**")
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.metric("Revenue", format_valeur(rev, devise))
                    with col_e2:
                        st.metric("Net Income", format_valeur(net, devise))
                else:
                    st.info("Aucune donnée trouvée pour ce ticker sur FMP.")

    except Exception as e:
        st.error(f"Erreur avec {ticker} : {e}")