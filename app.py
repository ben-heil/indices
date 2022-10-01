import plotly.express as px
import streamlit as st

from indices.utils import get_heading_names, load_text, get_pair_names, load_percentile_data, load_journal_data

# TODO decide whether to move the web app into the original repo or leave it here

if __name__ == '__main__':
    # Header
    header_text = load_text('app_files/header_text.md')
    st.write(header_text)

    heading_names = get_heading_names()
    heading1 = st.selectbox('Field of interest', heading_names)

    # Names of headings who have dfs paired with selected heading
    pair_names = get_pair_names(heading1)

    heading2 = st.selectbox('Heading 2', pair_names)

    percentile_data = load_percentile_data(heading1, heading2)

    fig = px.scatter(percentile_data, x=f'{heading1}_pagerank', y=f'{heading2}_pagerank', log_x=True, log_y=True,
                 opacity=1, color=f'{heading1}-{heading2}', color_continuous_scale='oxy', hover_data=['doi', 'title'],
                 title=f'Relative importance of papers in {heading1} and {heading2}',)

    st.plotly_chart(fig)

    journal_data = load_journal_data(heading1, heading2)

    fig = px.scatter(journal_data, x=f'{heading1}_pagerank', y=f'{heading2}_pagerank',
                     log_x=True, log_y=True, opacity=1, color=f'{heading1}-{heading2}',
                     color_continuous_scale='oxy', hover_data=['journal_title'],
                     title=f'Relative importance of papers in {heading1} and {heading2}',)
    st.plotly_chart(fig)
