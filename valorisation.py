import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import feedparser
import base64
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import time

# 1. Configuration de base
st.set_page_config(page_title="Value Quest", layout="centered")

# 2. Barre de titre
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

logo_base64 = get_base64_image("logo.png")
logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="nav-logo">' if logo_base64 else "🪙"

st.markdown(f"""
<style>
    header {{visibility: hidden !important;}}
    footer {{visibility: hidden !important;}}
    #MainMenu {{visibility: hidden !important;}}
    .block-container {{padding-top: 6rem !important;}}
    .nav-bar {{
        background-color: #001f3f !important; border-bottom: 3px solid #C0C0C0; padding: 12px;
        position: fixed; top: 0; left: 0; width: 100%; z-index: 99999; display: flex;
        align-items: center; justify-content: center; box-shadow: 0px 5px 15px rgba(0,0,0,0.4);
    }}
    .nav-logo {{height: 35px; margin-right: 15px;}}
    .nav-title {{
        color: #FEF9ED !important; font-size: 24px; font-weight: 700; letter-spacing: 1.5px;
        text-transform: uppercase; font-family: "Source Sans Pro", sans-serif; margin: 0;
    }}
    .stApp {{background-color: #fffdf4;}}
    .stMainBlockContainer *:not(.nav-bar):not(.nav-title) {{color: black !important; font-size: 15px !important;}}
    div[data-baseweb="select"] > div {{background-color: white !important;}}
    div[data-baseweb="popover"] ul {{background-color: white !important;}}
    div[data-baseweb="popover"] li {{background-color: white !important; color: black !important;}}
    div.stNumberInput input, div.stTextInput input {{background-color: white !important; color: black !important; border: 1px solid gray !important;}}
</style>
<div class="nav-bar">{logo_html}<span class="nav-title">VALUE QUEST</span></div>
""", unsafe_allow_html=True)

if "ping" in st.query_params:
    st.write("Pong! App is alive.")
    st.stop()

# 3. Fonctions optimisées (2 appels API MAX par ticker)
@st.cache_data(ttl=86400)
def fetch_search_results(query):
    try:
        return yf.Search(query, max_results=5).quotes
    except:
        return []

@st.cache_data(ttl=3600)
def get_ticker_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist_ytd = t.history(period="ytd")
        hist_full = t.history(period="5y")
        dividends = t.dividends.tail(5) if not t.dividends.empty else None
        return {"info": info, "hist_ytd": hist_ytd, "hist_full": hist_full, "dividends": dividends}
    except Exception as e:
        st.error(f"Erreur avec {ticker}: {e}")
        return None

# 4. Recherche principale
search_query = st.text_input("🔍 Rechercher une entreprise (nom ou ticker)", "", key="main_search_query")
ticker = None
if search_query and len(search_query) >= 3:
    try:
        quotes = fetch_search_results(search_query.lower())
        if quotes:
            options = [f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Sans nom'))}" for q in quotes]
            selected = st.selectbox("Sélectionnez l'entreprise :", options, key=f"selectbox_{search_query.lower()}")
            ticker = selected.split(" - ")[0]
        else:
            st.warning(f"Aucun résultat pour '{search_query}'")
    except:
        ticker = search_query.upper()
elif search_query and len(search_query) < 3:
    st.info("💡 Veuillez taper au moins 3 caractères pour lancer la recherche.")

# 5. Affichage des données si ticker valide
if ticker:
    data = get_ticker_data(ticker)
    if not data:
        st.error("Impossible de récupérer les données. Réessayez dans quelques minutes.")
        st.stop()

    infos = data["info"]
    hist_ytd = data["hist_ytd"]
    hist_full = data["hist_full"]
    dividends = data["dividends"]
    devise = infos.get("currencySymbol") or infos.get("currency") or ""
    prix = infos.get("currentPrice", 0)
    prev_close = infos.get("regularMarketPreviousClose")
    day_change = ((prix - prev_close) / prev_close) * 100 if isinstance(prix, (int, float)) and prev_close else 0
    day_color = "green" if day_change >= 0 else "red"
    day_text = f"({day_change:+.2f}%)" if isinstance(day_change, (int, float)) else ""

    # YTD Performance
    ytd_text = "N/A YTD"
    if not hist_ytd.empty and len(hist_ytd) > 0:
        try:
            price_jan_1st = hist_ytd['Close'].iloc[0]
            ytd_change = ((prix - price_jan_1st) / price_jan_1st) * 100
            ytd_text = f"{ytd_change:+.2f}% YTD"
        except:
            pass

    # Affichage entreprise
    company_name = infos.get("longName", infos.get("shortName", "Inconnu"))
    st.write(f"**Entreprise** : {company_name}")
    website = infos.get("website", "")
    if website:
        domain = website.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
        try:
            st.image(f"https://logos-api.apistemic.com/domain:{domain}", width=40)
        except:
            st.write("Logo non disponible")
    else:
        st.write("Pas de site web ou logo disponible")

    with st.expander("📄 Résumé de l'entreprise (Yahoo Finance)"):
        st.write(infos.get("longBusinessSummary", "Résumé non disponible"))

    # Prix actuel
    market_state = infos.get("marketState", "").upper()
    is_market_closed = market_state in ["POST", "PRE"] or (datetime.now().hour >= 22)
    post_market_price = infos.get("postMarketPrice") or infos.get("afterHoursPrice")
    pre_market_price = infos.get("preMarketPrice")

    if is_market_closed:
        if post_market_price:
            display_price, price_label = post_market_price, "Prix After-Hours"
            price_change = ((post_market_price - prev_close) / prev_close) * 100
        elif pre_market_price:
            display_price, price_label = pre_market_price, "Prix Pre-Market"
            price_change = ((pre_market_price - prev_close) / prev_close) * 100
        else:
            display_price, price_label, price_change = prix, "Prix de clôture", 0
    else:
        display_price, price_label, price_change = prix, "Prix actuel", day_change

    change_color = "green" if isinstance(price_change, (int, float)) and price_change >= 0 else "red"
    change_text = f"{price_change:+.2f}%" if isinstance(price_change, (int, float)) and price_change != 0 else "0%"

    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #001f3f;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 14px; color: #666; font-weight: bold;">{price_label}</span>
                <div style="font-size: 32px; font-weight: 700; color: black; margin-top: 5px;">{display_price:.2f} {devise}</div>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 14px; color: {change_color}; font-weight: bold;">{change_text}</span>
                <div style="font-size: 12px; color: #666; margin-top: 3px;">{ytd_text}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    market_cap = infos.get("marketCap")
    st.write(f"**Market Cap** : {market_cap / 1_000_000_000:,.2f} Mds {devise}" if market_cap else "**Market Cap** : N/A")

    def format_valeur(valeur, devise):
        if valeur is None or valeur == "N/A":
            return "N/A"
        abs_val = abs(valeur)
        return f"{valeur / 1_000_000_000:,.2f} Mds {devise}" if abs_val >= 1_000_000_000 else f"{valeur / 1_000_000:,.2f} M {devise}"

    # ONGLETS
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Ratios", "💰 Rentabilité", "📈 Prix juste", "📋 Earnings",
        "🧠 Actualités", "⚖️ Comparateur", "📈 Graphique", "🌍 Marchés Populaires", "🧮 Modèle DCF"
    ])

    with tab1:
        st.title("🔢 Ratios financiers")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**PER (trailing)** : {infos.get('trailingPE', 'N/A')}")
            st.write(f"**PER (forward)** : {infos.get('forwardPE', 'N/A')}")
            st.write(f"**EPS (trailing)** : {infos.get('trailingEps', 'N/A')}")
            ocf = infos.get("operatingCashflow")
            if ocf and market_cap and ocf > 0:
                st.write(f"**Price/OCF** : {market_cap / ocf:.2f}")
            else:
                st.write("**Price/OCF** : N/A")
            fcf = infos.get("freeCashflow")
            if fcf and market_cap and fcf > 0:
                st.write(f"**Price/FCF** : {market_cap / fcf:.2f}")
            else:
                st.write("**Price/FCF** : N/A")
            st.write(f"**Debt/Equity** : {infos.get('debtToEquity', 'N/A')}")

        with col2:
            capex = infos.get("capitalExpenditure")
            if capex is None and ocf and fcf:
                capex = ocf - fcf
            st.write(f"**CAPEX** : {format_valeur(abs(capex), devise) if capex else 'N/A'}")
            st.write(f"**Op Cash Flow** : {format_valeur(ocf, devise) if ocf else 'N/A'}")
            if ocf and ocf != 0 and capex is not None:
                st.write(f"**CAPEX/OCF** : {abs(capex) / ocf * 100:.1f} %")
            else:
                st.write("**CAPEX/OCF** : N/A")
            st.write(f"**Gross Margin** : {infos.get('grossMargins', 0) * 100:.1f} %" if infos.get('grossMargins') else "**Gross Margin** : N/A")
            st.write(f"**Profit Margin** : {infos.get('profitMargins', 0) * 100:.1f} %" if infos.get('profitMargins') else "**Profit Margin** : N/A")
            st.write(f"**Free Cash Flow** : {format_valeur(fcf, devise) if fcf else 'N/A'}")

        with col3:
            st.write(f"**ROE** : {infos.get('returnOnEquity', 0) * 100:.1f} %" if infos.get('returnOnEquity') else "**ROE** : N/A")
            st.write(f"**ROA** : {infos.get('returnOnAssets', 0) * 100:.1f} %" if infos.get('returnOnAssets') else "**ROA** : N/A")
            st.write(f"**Dividend Yield** : {infos.get('dividendYield', 0):.2f} %" if infos.get('dividendYield') else "**Dividend Yield** : N/A")
            st.write(f"**Price/Book** : {infos.get('priceToBook', 'N/A')}")
            total_debt = infos.get("totalDebt")
            if fcf and total_debt and fcf > 0:
                st.write(f"**Debt/FCF** : {total_debt / fcf:.2f} ans")
            else:
                st.write("**Debt/FCF** : N/A")
            shares = infos.get("sharesOutstanding")
            st.write(f"**Actions en circulation** : {shares:,.0f}" if shares else "**Actions** : N/A")

    with tab2:
        st.title("📊 Valorisation")
        horizon = st.number_input("Horizon (années)", min_value=1, max_value=30, value=5)
        cagr_eps = st.number_input("CAGR EPS estimé (%)", min_value=-100.0, value=12.0)
        eps_actuel = infos.get("trailingEps", 0.01)
        eps_futur = eps_actuel * ((1 + cagr_eps / 100) ** horizon)
        per_futur = st.number_input(f"PER dans {horizon} ans", min_value=5.0, value=20.0)
        prix_cible = eps_futur * per_futur
        st.write(f"**Prix cible dans {horizon} ans** : {prix_cible:.2f} {devise}")
        if isinstance(prix, (float, int)) and prix_cible > 0 and prix > 0:
            cagr_prix = ((prix_cible / prix) ** (1/horizon) - 1) * 100
            if cagr_prix >= 10:
                st.success(f"**CAGR** : {cagr_prix:.1f} %")
            else:
                st.error(f"**CAGR** : {cagr_prix:.1f} %")

    with tab3:
        st.title("💰 Prix d'entrée juste")
        cagr = st.number_input("Croissance EPS (%)", value=cagr_eps, key="cagr_tab3")
        rendement = st.number_input("Rendement attendu (%)", value=10.0)
        horizon = st.number_input("Horizon (années)", value=5, step=1, key="horizon_tab3")
        per = st.number_input("PER futur", min_value=5.0, value=20.0, key="per_tab3")
        prix_futur = eps_actuel * ((1 + cagr / 100) ** horizon) * per
        prix_juste = prix_futur / ((1 + rendement / 100) ** horizon)
        if isinstance(prix, (float, int)) and prix > 0:
            if prix_juste >= prix:
                st.success(f"**Prix juste** : {prix_juste:.2f} {devise} (✅ Bon point d'entrée)")
            else:
                st.error(f"**Prix juste** : {prix_juste:.2f} {devise} (⚠️ Surrévalué)")

    with tab4:
        st.title("🎙️ Calendrier & Dividendes")
        st.subheader("📅 Dates clés")
        c1, c2, c3 = st.columns(3)
        with c1:
            earn_date = infos.get('earningsTimestamp')
            st.metric("Prochains Earnings", datetime.fromtimestamp(earn_date).strftime('%d/%m/%Y') if earn_date else "N/A")
        with c2:
            ex_div_date = infos.get('exDividendDate')
            st.metric("Détachement Div.", datetime.fromtimestamp(ex_div_date).strftime('%d/%m/%Y') if ex_div_date else "N/A")
        with c3:
            div_date = infos.get('dividendDate')
            st.metric("Versement Div.", datetime.fromtimestamp(div_date).strftime('%d/%m/%Y') if div_date else "N/A")
        st.divider()
        st.subheader("💰 Derniers Dividendes")
        if dividends is not None and not dividends.empty:
            df_divs = dividends.to_frame().sort_index(ascending=False).head(5)
            df_divs.index = df_divs.index.strftime('%d/%m/%Y')
            df_divs.columns = ['Montant']
            st.table(df_divs)
        else:
            st.write("Cette entreprise ne verse pas de dividendes.")
        st.divider()
        st.subheader("🏢 Secteur & Insiders")
        sector = infos.get('sector', 'N/A')
        industry = infos.get('industry', 'N/A')
        if sector != 'N/A' or industry != 'N/A':
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #001f3f;">
                <p><strong>Secteur :</strong> {sector}</p>
                <p><strong>Industrie :</strong> {industry}</p>
            </div>
            """, unsafe_allow_html=True)
        insider_pct = infos.get('heldPercentInsiders', 0)
        if insider_pct:
            display_pct = insider_pct * 100 if insider_pct < 1 else insider_pct
            st.metric("👤 Insiders", f"{display_pct:.2f}%")

    with tab5:
        st.title(f"📰 Actualités : {company_name}")
        try:
            feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
            if feed.entries:
                for entry in feed.entries[:10]:
                    with st.container():
                        st.subheader(entry.title)
                        st.markdown(f'<a href="{entry.link}" target="_blank">🔗 Lire l\'article</a>', unsafe_allow_html=True)
                        st.divider()
            else:
                st.info("Aucune actualité trouvée.")
        except:
            st.error("Impossible de charger les actualités.")

    with tab6:
        st.title("⚖️ Comparateur")
        if "tickers_comparateurs" not in st.session_state:
            st.session_state.tickers_comparateurs = []
        if len(st.session_state.tickers_comparateurs) < 2:
            search_comp = st.text_input("Rechercher une entreprise à comparer", key="comp_search")
            if search_comp:
                quotes = fetch_search_results(search_comp.lower())
                if quotes:
                    options = [f"{q['symbol']} - {q.get('longname', 'N/A')}" for q in quotes]
                    selected = st.selectbox("Sélectionnez", options, key="comp_select")
                    ticker_to_add = selected.split(" - ")[0]
                    if st.button(f"➕ Ajouter {ticker_to_add}"):
                        if ticker_to_add != ticker and ticker_to_add not in st.session_state.tickers_comparateurs:
                            st.session_state.tickers_comparateurs.append(ticker_to_add)
                            st.rerun()
                else:
                    st.warning("Aucun résultat")
        else:
            st.info("Limite de 2 entreprises atteinte.")

        if st.session_state.tickers_comparateurs:
            st.write("**Entreprises à comparer :**")
            for t in st.session_state.tickers_comparateurs:
                cols = st.columns([4, 1])
                cols[0].write(f"• **{t}**")
                if cols[1].button(f"❌", key=f"del_{t}"):
                    st.session_state.tickers_comparateurs.remove(t)
                    st.rerun()

        tickers_to_compare = [ticker] + st.session_state.tickers_comparateurs
        if len(tickers_to_compare) > 1:
            st.markdown("---")
            st.subheader("📊 Comparaison")
            comparison_data = {}
            for t in tickers_to_compare:
                data_t = get_ticker_data(t)
                if data_t:
                    i = data_t["info"]
                    market_cap_val = i.get("marketCap", 0)
                    free_cash_flow_val = i.get("freeCashflow", 0)
                    total_revenue = i.get("totalRevenue", 0)
                    comparison_data[t] = {
                        "Nom": i.get("longName", "N/A"),
                        "Prix": f"{i.get('currentPrice', 0):.2f} {i.get('currencySymbol', '')}",
                        "Market Cap": f"{i.get('marketCap', 0)/1e9:.2f} Mds" if i.get('marketCap') else "N/A",
                        "Price/Sales": f"{market_cap_val/total_revenue:.2f}" if total_revenue and total_revenue > 0 else "N/A",
                        "PER": i.get("trailingPE", "N/A"),
                        "PER (Forward)": i.get("forwardPE", "N/A"),
                        "Price/FCF": f"{market_cap_val/free_cash_flow_val:.2f}" if free_cash_flow_val and free_cash_flow_val > 0 else "N/A",
                        
                        "PEG": i.get("pegRatio", "N/A"),
                        "Price/Book": i.get("priceToBook", "N/A"),
                        "Sector": i.get("sector", "N/A"),
                        "Dividend Yield": f"{i.get('dividendYield', 0):.2f} %" if i.get('dividendYield') else "N/A"
                    }
                time.sleep(0.5)
            if comparison_data:
                st.dataframe(pd.DataFrame(comparison_data).T, use_container_width=True)

    with tab7:
        st.title(f"📈 Graphique : {company_name}")
        period = st.selectbox("Période", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

        # Mapping des périodes en jours
        period_days = {
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825
        }

        try:
            df = hist_full.tail(period_days[period])
            if not df.empty:
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                )])
                fig.update_layout(
                    height=500,
                    paper_bgcolor='#fffdf4',
                    plot_bgcolor='white',
                    xaxis_rangeslider_visible=True,
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Aucune donnée historique.")
        except Exception as e:
            st.error(f"Erreur graphique : {e}")

    with tab8:
        st.title("🌍 Marchés Populaires")
        markets = {
            "📈 **Indices**": {
                "CAC 40": "^FCHI",
                "Nasdaq": "^IXIC",
                "S&P 500": "^GSPC",
                "Dow Jones": "^DJI"
            },
            "🛢️ **Matières Premières**": {
                "Or": "GC=F",
                "Pétrole Brent": "BZ=F",
                "Pétrole WTI": "CL=F"
            },
            "💱 **Devises**": {
                "EUR/USD": "EURUSD=X",
                "USD/JPY": "USDJPY=X",
                "GBP/USD": "GBPUSD=X"
            },
            "💵 **Obligations US**": {
                "US 2y": "^TNX",
                "US 10y": "^TYX"
            }
        }
        for category, items in markets.items():
            st.subheader(category)
            cols = st.columns(len(items))
            for idx, (name, symbol) in enumerate(items.items()):
                with cols[idx]:
                    try:
                        market_data = yf.Ticker(symbol)
                        price = market_data.history(period="1d")['Close'].iloc[-1]
                        
                        display_text = f"{price:.2f}"
                        if symbol == "^TYX":
                            st.session_state["us10y_rate"] = float(price)
                            display_text = f"{price:.2f}"

                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 8px; border-left: 4px solid #001f3f;">
                            <strong>{name}</strong><br><span style="font-size: 18px;">{display_text}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    except:
                        st.info(f"{name}: N/A")
            st.divider()

    with tab9:
        st.title("🧮 Modèle de Valorisation DCF Optimization")
        
        # MODIFICATION : Lecture directe depuis le dictionnaire d'API 'infos' qui est global et stable en mémoire
        fcf_api = infos.get("freeCashflow", 0.0)
        if fcf_api is None:
            fcf_api = 0.0
            
        beta_api = 1.0  # Calé par défaut à 1.00
        mcap_api = infos.get("marketCap", 1.0)
        
        total_debt_api = infos.get("totalDebt", 0.0)
        cash_api = infos.get("totalCash", 0.0)
        net_debt_api = total_debt_api - cash_api
        
        # MODIFICATION : Clonage de la clé d'origine brute pour empêcher la réinitialisation à 1
        shares_api = infos.get("sharesOutstanding", 1.0)
        if not shares_api or shares_api == 0:
            shares_api = 1.0
        
        # Récupération dynamique du US 10Y selon ton réglage actuel
        rf_api = st.session_state.get("us10y_rate", 40.0)
        
        # Calcul indicatif du coût brut de la dette
        interest_exp = infos.get("interestExpense", None)
        if interest_exp and total_debt_api > 0:
            calculated_rd = abs(interest_exp) / total_debt_api * 100
        else:
            calculated_rd = 4.0
            
        # Structure du Capital (%)
        total_ev_api = mcap_api + net_debt_api
        pct_equity_calc = (mcap_api / total_ev_api * 100) if total_ev_api > 0 else 100.0
        pct_debt_calc = (net_debt_api / total_ev_api * 100) if total_ev_api > 0 else 0.0
        pct_equity_calc = max(min(pct_equity_calc, 100.0), 0.0)
        pct_debt_calc = max(min(pct_debt_calc, 100.0), 0.0)

        st.subheader("1. Configuration des Inputs")
        
        col_inp1, col_inp2 = st.columns(2)
        with col_inp1:
            st.markdown("**📊 Flux & Croissance**")
            fcf_base = st.number_input(f"Free Cash Flow Année 1 ({devise})", value=float(fcf_api), format="%f", key="dcf_fcf_base")
            cagr_dcf = st.number_input("Taux de croissance explicite (Années 1 à 5 en %)", value=8.0, step=0.5, key="dcf_cagr")
            g_dcf = st.number_input("Taux de croissance à l'infini (g en %)", value=2.0, step=0.1, key="dcf_g")
            horizon_dcf = st.number_input("Horizon explicite (années)", min_value=1, max_value=20, value=5, step=1, key="dcf_horizon")
            
            st.markdown("**🏢 Bilan & Structure**")
            dette_nette_input = st.number_input(f"Dette Financière Nette ({devise})", value=float(net_debt_api), format="%f", key="dcf_net_debt")
            shares_input = st.number_input("Actions en circulation", value=int(shares_api), format="%d", key="dcf_shares")

        with col_inp2:
            st.markdown("**⚙️ Paramètres du WACC**")
            tax_rate = st.number_input("Taux d'impôt standard (%)", value=30.0, step=0.5, key="dcf_tax")
            mkt_premium = st.number_input("Prime de risque de marché globale (%)", value=6.0, step=0.1, key="dcf_premium")
            rf_rate = st.number_input("Taux sans risque (Obligation d'État 10Y %)", value=float(rf_api), step=0.1, key="dcf_rf")
            beta_input = st.number_input("Bêta de l'entreprise", value=float(beta_api), step=0.05, format="%.2f", key="dcf_beta")
            
            st.markdown("**⚖️ Coût des Financements**")
            pct_equity = st.number_input("Cible Capitaux Propres / EV (%)", value=float(pct_equity_calc), min_value=0.0, max_value=100.0, step=1.0, key="dcf_pct_eq")
            pct_debt = st.number_input("Cible Dette Nette / EV (%)", value=float(pct_debt_calc), min_value=0.0, max_value=100.0, step=1.0, key="dcf_pct_d")
            cost_of_debt = st.number_input("Coût brut de la dette (%)", value=float(calculated_rd), step=0.1, key="dcf_rd")

        if pct_equity + pct_debt != 100.0:
            st.warning("⚠️ Attention : La somme des structures capitaux propres + dette ne fait pas 100%. Le modèle réajustera la pondération au prorata.")

        # 2. Moteur de calcul du WACC (CMPC)
        w_equity = pct_equity / (pct_equity + pct_debt) if (pct_equity + pct_debt) > 0 else 1.0
        w_debt = pct_debt / (pct_equity + pct_debt) if (pct_equity + pct_debt) > 0 else 0.0
        
        ke = (rf_rate / 100.0) + beta_input * (mkt_premium / 100.0)
        kd_net = (cost_of_debt / 100.0) * (1.0 - (tax_rate / 100.0))
        wacc_calculated = (w_equity * ke) + (w_debt * kd_net)

        # 3. Projection des Flux et Actualisation
        flux_projetes = []
        flux_actualises = []
        wacc_factor = 1.0 + wacc_calculated
        
        current_fcf = fcf_base
        for yr in range(1, horizon_dcf + 1):
            current_fcf = current_fcf * (1.0 + (cagr_dcf / 100.0))
            flux_projetes.append(current_fcf)
            
            fcf_act = current_fcf / (wacc_factor ** yr)
            flux_actualises.append(fcf_act)

        somme_fcf_act = sum(flux_actualises)

        # 4. Calcul de la Valeur Terminale (Gordon Shapiro)
        g_rate = g_dcf / 100.0
        if wacc_calculated <= g_rate:
            st.error("❌ Erreur mathématique : Le WACC calculé doit être strictement supérieur au taux de croissance à l'infini (g). Ajustez vos paramètres.")
            st.stop()
            
        fcf_terminal = flux_projetes[-1] * (1.0 + g_rate)
        valeur_terminale = fcf_terminal / (wacc_calculated - g_rate)
        valeur_terminale_act = valeur_terminale / (wacc_factor ** horizon_dcf)

        # 5. Calcul de l'Equity Value (Valeur théorique de l'action)
        valeur_entreprise_dcf = somme_fcf_act + valeur_terminale_act
        valeur_equity_dcf = valeur_entreprise_dcf - dette_nette_input
        prix_theorique_action = valeur_equity_dcf / shares_input if shares_input > 0 else 0.0

        # 6. Affichage Synthétique
        st.markdown("---")
        st.subheader("2. Résultats de la Valorisation")

        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            st.metric("📈 WACC (CMPC) Calculé", f"{wacc_calculated * 100:.2f} %")
            st.write(f"*Coût FP (Ke) : {ke*100:.2f} %*")
            st.write(f"*Coût Dette Net (Kd) : {kd_net*100:.2f} %*")
        with col_res2:
            st.metric("🏢 Valeur d'Entreprise", f"{valeur_entreprise_dcf / 1e9:,.2f} Mds {devise}")
            st.write(f"*Cumul FCF Explicites : {somme_fcf_act / 1e9:,.2f} Mds*")
            st.write(f"*Valeur Terminale Act. : {valeur_terminale_act / 1e9:,.2f} Mds*")
        with col_res3:
            st.metric("💎 Valeur des Capitaux Propres", f"{valeur_equity_dcf / 1e9:,.2f} Mds {devise}")
            st.write(f"*Dette Nette Déduite : {dette_nette_input / 1e9:,.2f} Mds*")

        st.markdown("### Évaluation du Cours")

        if prix_theorique_action > prix:
            potentiel = ((prix_theorique_action / prix) - 1.0) * 100.0
            st.success(f"🎯 **Prix Théorique du DCF : {prix_theorique_action:.2f} {devise}** (Potentiel de {potentiel:+.1f} % vs cours actuel de {prix:.2f} {devise} : ✅ Sous-évalué)")
        else:
            potentiel = ((prix_theorique_action / prix) - 1.0) * 100.0
            st.error(f"🎯 **Prix Théorique du DCF : {prix_theorique_action:.2f} {devise}** (Potentiel de {potentiel:+.1f} % vs cours actuel de {prix:.2f} {devise} : ⚠️ Surévalué)")

        with st.expander("📊 Détail des flux de trésorerie projetés année par année"):
            annees_label = [f"Année {i}" for i in range(1, horizon_dcf + 1)]
            df_flux = pd.DataFrame({
                "Flux de Trésorerie Projeté": [f"{f / 1e6:,.1f} M {devise}" for f in flux_projetes],
                "Facteur d'Actualisation": [f"1 / {wacc_factor ** i:.3f}" for i in range(1, horizon_dcf + 1)],
                "Flux Actualisé": [f"{f_act / 1e6:,.1f} M {devise}" for f_act in flux_actualises]
            }, index=annees_label)
            st.table(df_flux)
