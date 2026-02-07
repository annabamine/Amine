import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt


st.markdown("""
<style>
.stApp {
    background-color: #fffdf4;
}
.stApp * {
    color: black !important;
    font-size: 15px !important;
}
div, p, span, label, .stMarkdown, .stWrite, .stText, .stNumberInput label, .stTextInput label, .stHeader, .stAlert, .stSuccess, .stWarning, .stError {
    color: black !important;
    font-size: 15px !important;
}
div.stNumberInput input, div.stTextInput input {
    background-color: white !important;
    color: black !important;
    border: 1px solid gray !important;
    font-size: 15px !important;
}
header, .stAppHeader {
    background-color: #fffdf4 !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

ticker = st.text_input("Entre le ticker", "AAPL")

if ticker:
    try:
        action = yf.Ticker(ticker)
        infos = action.info
        devise = infos.get("currencySymbol") or infos.get("currency")
        prix = infos.get("currentPrice", "Non dispo")
        eps = infos.get("trailingEps", "Non dispo")
        per = infos.get("trailingPE", "Non dispo")
        fper = infos.get("forwardPE", "Non dispo")

        # Ajout : Nom de l'entreprise 
        company_name = infos.get("longName", infos.get("shortName", "Inconnu"))
        st.write(f"**Entreprise** : {company_name}")
        
        website = infos.get("website", "")
        if website:
            # Extrait le domaine propre (ex: apple.com)
            domain = website.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
            logo_url = f"https://logos-api.apistemic.com/domain:{domain}"
            try:
                st.image(logo_url, width=40)
            except:
                st.write("Logo non disponible")
        else:
            st.write("Pas de site web ou logo disponible")

        # Résumé
        summary = infos.get("longBusinessSummary", "Résumé non disponible sur Yahoo")
        with st.expander("📄 Résumé de l'entreprise (Yahoo Finance)"):
            st.write(summary)

        # Prix AVANT les onglets
        st.write(f"**Prix actuel** : {prix} {devise}")

        # Capitalisation boursière
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
        
        # Créer les onglets
        tab1, tab2, tab3 = st.tabs(["🔢 Ratios", "📊 Méthode 1", "💰 Méthode 2"])
        
        # ONGLET 1 : RATIOS
        with tab1:
            st.title("🔢 Ratios financiers")
            
            # 3 colonnes pour les ratios
            col1, col2, col3 = st.columns(3)
            
            # Colonne 1 : PER, Forward PER, EPS
            with col1:
                st.write(f"**PER (trailing)** : {per}")
                st.write(f"**PER (forward)** : {fper}")
                st.write(f"**EPS (trailing)** : {eps}")
                
                # Debt-to-Equity
                debt_to_equity = infos.get("debtToEquity")
                if debt_to_equity is not None:
                    st.write(f"**Debt/Equity** : {debt_to_equity:.2f}%")
                else:
                    st.write("**Debt/Equity** : N/A")

                # Price-to-Free Cash Flow (TTM)
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
            
            # Colonne 2 : CAPEX, OCF, CAPEX/OCF (TTM)
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
            
            # Colonne 3 : ROE, ROA
            with col3:
                # ROE
                roe = infos.get("returnOnEquity")
                if roe is not None:
                    roe_pct = roe * 100
                    st.write(f"**ROE** : {roe_pct:.1f} %")
                else:
                    st.write("**ROE** : N/A")
                
                # ROA
                roic = infos.get("returnOnAssets")
                if roic is not None:
                    roic_pct = roic * 100
                    st.write(f"**ROA** : {roic_pct:.1f} %")
                else:
                    st.write("**ROA** : N/A")

                # Dividend Yield
                dividend_yield = infos.get("dividendYield")
                if dividend_yield is not None:
                    st.write(f"**Dividend Yield** : {dividend_yield:.2f} %")
                else:
                    st.write("**Dividend Yield** : N/A")

                # Price-to-Book
                price_to_book = infos.get("priceToBook")
                if price_to_book is not None:
                    st.write(f"**Price/Book** : {price_to_book:.2f}")
                else:
                    st.write("**Price/Book** : N/A")

                # Debt-to-Free Cash Flow (TTM)
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

                # --- Évolution du nombre d'actions sur 5 ans (Bloc robuste) ---
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
                except Exception:
                    st.write("**Actions (évol.)** : N/A")
        
        # ONGLET 2 : MÉTHODE 1
        with tab2:
            st.title("📊 Méthode 1 - Estimation simple")
            
            cagr_eps = st.number_input("Mon CAGR estimé pour les EPS (en %)", min_value=-100.0, value=12.0)
            eps_actuel = infos.get("trailingEps", 0.01)
            eps_futur = eps_actuel * ((1 + cagr_eps / 100) ** 5)
            per_estime = st.number_input("PER que j'estime dans 5 ans", min_value=5.0, value=20.0)
            prix_cible = eps_futur * per_estime
            st.write(f"**Prix cible dans 5 ans** : {prix_cible:.2f} {devise}")

            if isinstance(prix, (float, int)) and prix_cible > 0 and prix > 0:
                cagr_prix = ((prix_cible / prix) ** (1/5) - 1) * 100
                if cagr_prix >= 10:
                    st.success(f"**CAGR au prix actuel (5 ans)** : {cagr_prix:.1f} %")
                else:
                    st.error(f"**CAGR au prix actuel (5 ans)** : {cagr_prix:.1f} %")
        
        # ONGLET 3 : MÉTHODE 2
        with tab3:
            st.title("💰 Méthode 2 - Prix d'entrée juste")

            rendement_attendu = st.number_input("Rendement annuel attendu (%)", value=10.0)
            horizon = st.number_input("Nombre d'années", value=5, step=1)
            per_futur = st.number_input("PER que j'estime à l'horizon", min_value=5.0, value=20.0)

            prix_futur = eps_actuel * ((1 + cagr_eps / 100) ** horizon) * per_futur
            prix_entree = prix_futur / ((1 + rendement_attendu / 100) ** horizon)
            
            if isinstance(prix, (float, int)) and prix > 0 and prix_futur > 0:
                implied_cagr = ((prix_futur / prix) ** (1/horizon) - 1) * 100
                if prix_entree >= prix:
                    st.success(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
                else:
                    st.error(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
        
    except Exception as e:
        st.error(f"Erreur avec {ticker} : {e}")