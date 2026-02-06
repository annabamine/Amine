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
    font-size: 15px !important;  /* ← augmenté */
}
div, p, span, label, .stMarkdown, .stWrite, .stText, .stNumberInput label, .stTextInput label, .stHeader, .stAlert, .stSuccess, .stWarning, .stError {
    color: black !important;
    font-size: 15px !important;
}
div.stNumberInput input, div.stTextInput input {
    background-color: white !important;
    color: black !important;
    border: 1px solid gray !important;
    font-size: 15px !important;  /* ← aussi pour ce qu'on tape */
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

        st.title("🔢 Ratios financiers")


        st.write(f"**Prix actuel** : {prix} {devise}")
        st.write(f"**PER (trailing)** : {per}")
        st.write(f"**PER (forward)** : {fper}")
        st.write(f"**EPS (trailing)** : {eps}")


    
        # Récupération des données financières
        roe = infos.get("returnOnEquity")
        roic = infos.get("returnOnAssets")  # Yahoo n'a pas toujours ROIC, ROA est similaire
        
        # Données des cash flows
        try:
            cashflow = action.cashflow
            if not cashflow.empty:
                # Prend les données les plus récentes (première colonne)
                capex = cashflow.loc["Capital Expenditure"].iloc[0] if "Capital Expenditure" in cashflow.index else None
                operating_cash_flow = cashflow.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cashflow.index else None
                
                # Affichage CAPEX
                if capex is not None:
                    capex_millions = capex / 1_000_000
                    st.write(f"**CAPEX** : {capex_millions:,.0f} M {devise}")
                else:
                    st.write("**CAPEX** : Non disponible")
                
                # Affichage Operating Cash Flow
                if operating_cash_flow is not None:
                    ocf_millions = operating_cash_flow / 1_000_000
                    st.write(f"**Operating Cash Flow** : {ocf_millions:,.0f} M {devise}")
                else:
                    st.write("**Operating Cash Flow** : Non disponible")
                
                # Ratio CAPEX / Operating Cash Flow
                if capex is not None and operating_cash_flow is not None and operating_cash_flow != 0:
                    ratio_capex_ocf = abs(capex) / operating_cash_flow * 100
                    st.write(f"**CAPEX / Op Cash Flow** : {ratio_capex_ocf:.1f} %")
                else:
                    st.write("**CAPEX / Op Cash Flow** : Non disponible")
            else:
                st.write("**CAPEX** : Non disponible")
                st.write("**Operating Cash Flow** : Non disponible")
                st.write("**CAPEX / Op Cash Flow** : Non disponible")
        except:
            st.write("**CAPEX** : Non disponible")
            st.write("**Operating Cash Flow** : Non disponible")
            st.write("**CAPEX / Op Cash Flow** : Non disponible")
        
        # ROE
        if roe is not None:
            roe_pct = roe * 100
            st.write(f"**ROE (Return on Equity)** : {roe_pct:.1f} %")
        else:
            st.write("**ROE** : Non disponible")
        
        # ROIC (ou ROA si ROIC pas dispo)
        if roic is not None:
            roic_pct = roic * 100
            st.write(f"**ROA (Return on Assets)** : {roic_pct:.1f} %")
        else:
            st.write("**ROIC/ROA** : Non disponible")




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




        st.title("💰 Méthode 2 - Prix d'entrée juste")


        rendement_attendu = st.number_input("Rendement annuel attendu (%)", value=10.0)
        horizon = st.number_input("Nombre d'années", value=5, step=1)
        per_futur = st.number_input("PER que j'estime à l'horizon", min_value=5.0, value=20.0)

        prix_futur = eps_actuel * ((1 + cagr_eps / 100) ** horizon) * per_futur
        prix_entree = prix_futur / ((1 + rendement_attendu / 100) ** horizon)
        

        if isinstance(prix, (float, int)) and prix > 0 and prix_futur > 0:
            implied_cagr = ((prix_futur / prix) ** (1/horizon) - 1) * 100
            if prix_entree >= prix:  # équivalent à implied_cagr >= rendement_attendu
                st.success(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
            else:
                st.error(f"**Prix d'entrée juste aujourd'hui** : {prix_entree:.2f} {devise}")
        

        
    except Exception as e:
        st.error(f"Erreur avec {ticker} : {e}")
