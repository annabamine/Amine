import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt

# Configuration du style
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
        devise = infos.get("currencySymbol") or infos.get("currency") or "$"
        prix = infos.get("currentPrice")
        eps = infos.get("trailingEps", "Non dispo")
        per = infos.get("trailingPE", "Non dispo")
        fper = infos.get("forwardPE", "Non dispo")

        # Ajout : Nom de l'entreprise 
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

        # Résumé
        summary = infos.get("longBusinessSummary", "Résumé non disponible sur Yahoo")
        with st.expander("📄 Résumé de l'entreprise"):
            st.write(summary)

        # Prix et Market Cap
        st.write(f"**Prix actuel** : {prix} {devise}")
        market_cap = infos.get("marketCap")
        if market_cap:
            st.write(f"**Market Cap** : {market_cap / 1_000_000_000:,.2f} Mds {devise}")

        # Créer les onglets
        tab1, tab2, tab3 = st.tabs(["🔢 Ratios", "📊 Méthode 1", "💰 Méthode 2"])
        
        # ONGLET 1 : RATIOS
        with tab1:
            st.title("🔢 Ratios financiers")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**PER (trailing)** : {per}")
                st.write(f"**PER (forward)** : {fper}")
                st.write(f"**EPS (trailing)** : {eps}")
                
                debt_to_equity = infos.get("debtToEquity")
                st.write(f"**Debt/Equity** : {f'{debt_to_equity:.2f}%' if debt_to_equity else 'N/A'}")

                # Price-to-FCF
                try:
                    fcf = infos.get("freeCashflow")
                    if fcf and market_cap:
                        st.write(f"**Price/FCF** : {market_cap / fcf:.2f}")
                    else:
                        st.write("**Price/FCF** : N/A")
                except:
                    st.write("**Price/FCF** : N/A")
            
            with col2:
                try:
                    cashflow = action.cashflow
                    if not cashflow.empty:
                        capex = cashflow.loc["Capital Expenditure"].iloc[0] if "Capital Expenditure" in cashflow.index else None
                        ocf = cashflow.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cashflow.index else None
                        
                        st.write(f"**CAPEX** : {abs(capex)/1_000_000:,.0f} M {devise}" if capex else "**CAPEX** : N/A")
                        st.write(f"**Op Cash Flow** : {ocf/1_000_000:,.0f} M {devise}" if ocf else "**Op Cash Flow** : N/A")
                        
                        if capex and ocf:
                            st.write(f"**CAPEX/OCF** : {abs(capex)/ocf*100:.1f} %")
                    else:
                        st.write("**CAPEX/OCF** : N/A")
                except:
                    st.write("**CAPEX/OCF** : N/A")
                
                margin = infos.get("profitMargins")
                st.write(f"**Profit Margin** : {margin*100:.1f} %" if margin else "**Profit Margin** : N/A")

            with col3:
                roe = infos.get("returnOnEquity")
                st.write(f"**ROE** : {roe*100:.1f} %" if roe else "**ROE** : N/A")
                
                roa = infos.get("returnOnAssets")
                st.write(f"**ROA** : {roa*100:.1f} %" if roa else "**ROA** : N/A")

                div = infos.get("dividendYield")
                st.write(f"**Dividend Yield** : {div*100:.2f} %" if div else "**Dividend Yield** : N/A")
                
                pb = infos.get("priceToBook")
                st.write(f"**Price/Book** : {pb:.2f}" if pb else "**Price/Book** : N/A")

                # Évolution actions
                try:
                    shares = action.get_shares_full(start="2021-01-01")
                    if not shares.empty:
                        change = ((shares.iloc[-1] - shares.iloc[0]) / shares.iloc[0]) * 100
                        emoji = "📈" if change > 0 else "📉"
                        st.write(f"**Actions (évol.)** : {change:+.1f} % {emoji}")
                    else:
                        st.write("**Actions (évol.)** : N/A")
                except:
                    st.write("**Actions (évol.)** : N/A")
        
        # ONGLET 2 : MÉTHODE 1
        with tab2:
            st.title("📊 Méthode 1 - Estimation simple")
            cagr_eps = st.number_input("Mon CAGR estimé pour les EPS (en %)", min_value=-100.0, value=12.0)
            eps_actuel = float(eps) if isinstance(eps, (int, float)) else 0.01
            eps_futur = eps_actuel * ((1 + cagr_eps / 100) ** 5)
            per_estime = st.number_input("PER que j'estime dans 5 ans", min_value=5.0, value=20.0)
            prix_cible = eps_futur * per_estime
            st.write(f"**Prix cible dans 5 ans** : {prix_cible:.2f} {devise}")

            if prix and prix > 0:
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
            per_futur = st.number_input("PER que j'estime à l'horizon", min_value=5.0, value=20.0, key="m2_per")

            prix_futur = eps_actuel * ((1 + cagr_eps / 100) ** horizon) * per_futur
            prix_entree = prix_futur / ((1 + rendement_attendu / 100) ** horizon)
            
            if prix and prix > 0:
                if prix_entree >= prix:
                    st.success(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
                else:
                    st.error(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
        
    except Exception as e:
        st.error(f"Erreur avec {ticker} : {e}")