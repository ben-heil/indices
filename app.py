import numpy as np
import plotly.express as px
import streamlit as st

from indices import utils

ALL_JOURNAL_STR = 'All Journals'

if __name__ == '__main__':
    # Header
    header_text = utils.load_text('app_files/header_text.md')
    st.write(header_text)

    heading_names = utils.get_heading_names()
    heading_names.sort()
    heading1 = st.selectbox('Field 1', heading_names)

    # Names of headings who have dfs paired with selected heading
    pair_names = utils.get_pair_names(heading1)
    pair_names.sort()

    heading2 = st.selectbox('Field 2', pair_names)

    percentile_data = utils.load_percentile_data(heading1, heading2)
    journal_data = utils.load_journal_data(heading1, heading2)

    journal_names = utils.get_journal_names(journal_data)
    journal_names.sort()
    journal_names.insert(0, ALL_JOURNAL_STR)
    journal = st.selectbox('Journal To Highlight', journal_names)

    articles = len(percentile_data)

    if journal != ALL_JOURNAL_STR:
        opacities = np.where(percentile_data['journal'] == journal, 1, 100 / articles)
    else:
        opacities = 1

    color_scale =[(0, "red"), (0.5, "#d4d4d4"), (1, "blue")]

    fig = px.scatter(percentile_data, x=f'{heading1}_pagerank', y=f'{heading2}_pagerank', log_x=True, log_y=True,
                 opacity=opacities, color=f'{heading1}-{heading2}', hover_data=['doi', 'title'],
                 title=f'Relative importance of papers in {heading1} and {heading2}',
                 color_continuous_scale=color_scale,
                 range_color=(-1,1))

    st.plotly_chart(fig)

    fig = px.scatter(journal_data, x=f'{heading1}_pagerank', y=f'{heading2}_pagerank',
                     log_x=True, log_y=True, opacity=1,
                     hover_data=['journal_title'],
                     title=f'Common journals in {heading1} and {heading2}',
                     color_discrete_sequence=['black'])
    st.plotly_chart(fig)
