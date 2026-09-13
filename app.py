import streamlit as st
import pandas as pd
import dhlab.text as dh
import dhlab.api.dhlab_api as api
from urllib.parse import quote

# -----------------
# Konfigurasjon
# -----------------
st.set_page_config(layout="wide", page_title="BBI - Barnebokkorpus", initial_sidebar_state="auto")
st.title("Søk og analyse i Barnebokkorpuset (BBI)")

# -----------------
# Datalasting
# -----------------
@st.cache_data(show_spinner="Laster korpus fra data/barn.csv...")
def last_korpus():
    df = pd.read_csv('data/barn.csv', low_memory=False)
    
    # Sørg for at dhlabid eller urn brukes
    c = dh.Corpus()
    if 'urn' in df.columns:
        urns = df['urn'].dropna().unique().tolist()
        try:
            c.extend_from_identifiers(urns)
        except Exception as e:
            st.warning("Kunne ikke utvide dhlab-korpus fra identifikatorer.")
            print(e)
    return df, c

try:
    df_meta, corpus = last_korpus()
except FileNotFoundError:
    st.error("Fant ikke data/barn.csv. Sørg for at filen ligger i 'data'-mappen.")
    st.stop()

# -----------------
# Grensesnitt
# -----------------
tabs = st.tabs(["Konkordans", "Trender / N-gram", "Metadata"])

with tabs[0]:
    st.subheader("Konkordans (Konk)")
    search_konk = st.text_input('Søkeord:', "", help="Bruk anførselstegn for fraser, f.eks. \"spise opp\"")
    limit_konk = st.number_input("Maks antall treff:", min_value=10, max_value=10000, value=150)
    
    if st.button("Søk i konkordans") and search_konk:
        with st.spinner("Søker..."):
            urns = df_meta['urn'].dropna().unique().tolist()
            try:
                # Gjør API-kall til dhlab
                res = api.concordance(urns, search_konk, limit=limit_konk)
                
                if res is not None and not res.empty:
                    conc = res[["urn", "conc"]].rename(columns={"conc": "concordance"})
                    # Koble på våre egne metadata
                    konkdf = conc.merge(df_meta, on='urn', how='left')
                    
                    # Rense HTML for markdown-visning
                    konkdf['concordance'] = konkdf['concordance'].apply(lambda x: str(x).replace('<b>', '**').replace('</b>', '**'))
                    
                    # Formater lenker
                    konkdf['nb_lenke'] = konkdf['urn'].apply(lambda x: f"https://www.nb.no/items/{x}?searchText={quote(search_konk)}")
                    
                    visnings_df = konkdf[['nb_lenke', 'year', 'authors', 'title', 'concordance']].sort_values('year')
                    
                    st.markdown(f"Fant **{len(visnings_df)}** treff.")
                    
                    st.dataframe(
                        visnings_df, 
                        column_config={
                            "nb_lenke": st.column_config.LinkColumn("Nasjonalbiblioteket", display_text="Åpne i NB"),
                            "year": st.column_config.NumberColumn("År", format="%d"),
                            "authors": "Forfatter",
                            "title": "Tittel",
                            "concordance": "Kontekst"
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Ingen treff på dette søkeordet.")
            except Exception as e:
                st.error(f"Feil ved søk: {e}")

with tabs[1]:
    st.subheader("Trender (N-gram)")
    st.write("Her kan vi koble på dhlab for å telle ord og vise trender over tid.")
    search_trend = st.text_input("Ord for trendanalyse (komma-separert):", "barn, skole, leke")
    
    if st.button("Generer Trendlinjer"):
        words = [w.strip() for w in search_trend.split(',')]
        if corpus.frame.empty:
            st.warning("Korpuset er tomt, kan ikke beregne trender.")
        else:
            with st.spinner("Beregner trender..."):
                try:
                    # Merk: avhengig av dhlab-versjon og korpusstørrelse kan Ngram fungere ulikt
                    # Vi legger inn et placeholder-kall her som kan utvides senere.
                    st.info("Trendanalyse-funksjonalitet må kodes inn med dh.Ngram eller api.get_document_frequencies(). Sjekker dokumentasjon...")
                except Exception as e:
                    st.error(f"Feil ved beregning: {e}")

with tabs[2]:
    st.subheader(f"Oversikt over data (Totalt {len(df_meta)} dokumenter)")
    st.dataframe(df_meta.head(100), use_container_width=True)
