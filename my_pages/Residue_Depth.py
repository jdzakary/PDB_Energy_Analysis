import pandas as pd
import streamlit as st
from typing import Dict
from bokeh.plotting import figure, ColumnDataSource


def check_files(file_name: str) -> bool:
    constraints = [
        f'depth_{file_name}' in st.session_state.keys(),
        f'energy_{file_name}' in st.session_state.keys()
    ]
    return all(constraints)


def plot(file_name: str) -> None:
    interactions: pd.DataFrame = st.session_state[f'energy_{file_name}']
    depth: Dict[int: float] = st.session_state[f'depth_{file_name}']
    resi = interactions['resi1'].values.tolist() + \
        interactions['resi2'].values.tolist()
    assert max(resi) == max(depth.keys())
    assert min(resi) == min(depth.keys()) == 1

    net_energy = {}
    for i in depth.keys():
        query = interactions[
            (interactions['resi1'] == i) |
            (interactions['resi2'] == i)
            ]
        net_energy[i] = query['total'].sum()

    source = ColumnDataSource(
        data=dict(
            x=list(depth.values()),
            y=list(net_energy.values()),
            position=list(depth.keys())
        )
    )
    tool_tips = [
        ('Position', '@position'),
        ('Depth', '@x'),
        ('Net Energy', '@y')
    ]
    plot = figure(tooltips=tool_tips)
    plot.title = 'Net Energy vs Depth for Individual Residues'
    plot.xaxis.axis_label = 'Residue Depth from Surface'
    plot.yaxis.axis_label = 'Net Interaction Energy'

    scatter = plot.circle()
    scatter.data_source = source
    scatter.glyph.size = 6
    st.bokeh_chart(plot, use_container_width=True)


def main():
    st.title('Residue Depth in the Protein')
    st.subheader('Wild-Type Structure')
    if check_files('wild'):
        plot('wild')
    else:
        st.error('Not all Pre-requisites are calculated')

    st.subheader('Variant Structure')
    if check_files('variant'):
        plot('variant')
    else:
        st.error('Not all Pre-requisites are calculated')


if __name__ == '__main__':
    main()
