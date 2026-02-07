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

                # Price-to-Free Cash Flow
                try:
                    cashflow = action.cashflow
                    if not cashflow.empty:
                        free_cash_flow = cashflow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cashflow.index else None
                        market_cap = infos.get("marketCap")
                        
                        if free_cash_flow is not None and market_cap is not None and free_cash_flow > 0:
                            price_to_fcf = market_cap / free_cash_flow
                            st.write(f"**Price/FCF** : {price_to_fcf:.2f}")
                        else:
                            st.write("**Price/FCF** : N/A")
                    else:
                        st.write("**Price/FCF** : N/A")
                except:
                    st.write("**Price/FCF** : N/A")
            
            # Colonne 2 : CAPEX, OCF, CAPEX/OCF
            with col2:
                try:
                    cashflow = action.cashflow
                    if not cashflow.empty:
                        capex = cashflow.loc["Capital Expenditure"].iloc[0] if "Capital Expenditure" in cashflow.index else None
                        operating_cash_flow = cashflow.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cashflow.index else None
                        
                        # CAPEX
                        if capex is not None:
                            capex_billions = capex / 1_000_000_000
                            st.write(f"**CAPEX** : {capex_billions:,.2f} Mds {devise}")
                        else:
                            st.write("**CAPEX** : N/A")
                        
                        # Operating Cash Flow
                        if operating_cash_flow is not None:
                            ocf_billions = operating_cash_flow / 1_000_000_000
                            st.write(f"**Op Cash Flow** : {ocf_billions:,.2f} Mds {devise}")
                        else:
                            st.write("**Op Cash Flow** : N/A")
                        
                        # Ratio CAPEX/OCF
                        if capex is not None and operating_cash_flow is not None and operating_cash_flow != 0:
                            ratio_capex_ocf = abs(capex) / operating_cash_flow * 100
                            st.write(f"**CAPEX/OCF** : {ratio_capex_ocf:.1f} %")
                        else:
                            st.write("**CAPEX/OCF** : N/A")
                    else:
                        st.write("**CAPEX** : N/A")
                        st.write("**Op Cash Flow** : N/A")
                        st.write("**CAPEX/OCF** : N/A")
                except:
                    st.write("**CAPEX** : N/A")
                    st.write("**Op Cash Flow** : N/A")
                    st.write("**CAPEX/OCF** : N/A")
                
                # Profit Margin
                profit_margin = infos.get("profitMargins")
                if profit_margin is not None:
                    profit_margin_pct = profit_margin * 100
                    st.write(f"**Profit Margin** : {profit_margin_pct:.1f} %")
                else:
                    st.write("**Profit Margin** : N/A")

                # Free Cash Flow
                try:
                    cashflow = action.cashflow
                    if not cashflow.empty:
                        free_cash_flow = cashflow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cashflow.index else None
                        
                        if free_cash_flow is not None:
                            fcf_billions = free_cash_flow / 1_000_000_000
                            st.write(f"**Free Cash Flow** : {fcf_billions:,.2f} Mds {devise}")
                        else:
                            st.write("**Free Cash Flow** : N/A")
                    else:
                        st.write("**Free Cash Flow** : N/A")
                except:
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

                # Debt-to-Free Cash Flow
                try:
                    cashflow = action.cashflow
                    balance_sheet = action.balance_sheet
                    
                    if not cashflow.empty and not balance_sheet.empty:
                        free_cash_flow = cashflow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cashflow.index else None
                        total_debt = balance_sheet.loc["Total Debt"].iloc[0] if "Total Debt" in balance_sheet.index else None
                        
                        if free_cash_flow is not None and total_debt is not None and free_cash_flow > 0:
                            debt_to_fcf = total_debt / free_cash_flow
                            st.write(f"**Debt/FCF** : {debt_to_fcf:.2f} ans")
                        else:
                            st.write("**Debt/FCF** : N/A")
                    else:
                        st.write("**Debt/FCF** : N/A")
                except:
                    st.write("**Debt/FCF** : N/A")

                # --- Évolution du nombre d'actions sur 5 ans (Bloc robuste) ---
                try:
                    # On récupère les bilans annuels (qui remontent sur 4 ou 5 ans)
                    bs = action.balance_sheet
                    
                    # Liste de clés potentielles utilisées par Yahoo pour le nombre d'actions
                    keys_to_check = ["Ordinary Shares Number", "Share Issued", "Total Common Shares Outstanding"]
                    shares_series = None
                    
                    for key in keys_to_check:
                        if key in bs.index:
                            shares_series = bs.loc[key]
                            break
                            
                    if shares_series is not None and len(shares_series) >= 2:
                        shares_series = shares_series.dropna()
                        
                        shares_recent = shares_series.iloc[0] # Plus récente
                        shares_old = shares_series.iloc[-1]   # Plus ancienne
                        
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