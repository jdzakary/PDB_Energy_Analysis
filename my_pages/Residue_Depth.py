import pandas as pd
import streamlit as st
from typing import Dict, List
from bokeh.plotting import figure, ColumnDataSource


def check_files(file_name: str) -> bool:
    constraints = [
        f'depth_{file_name}' in st.session_state.keys(),
        f'energy_{file_name}' in st.session_state.keys()
    ]
    if file_name == 'variant':
        constraints.extend([
            f'depth_wild' in st.session_state.keys(),
            f'energy_wild' in st.session_state.keys()
        ])
    return all(constraints)


def changes() -> Dict[str, List[int]]:
    wild: pd.DataFrame = st.session_state['energy_wild']
    variant: pd.DataFrame = st.session_state['energy_variant']
    mutations: pd.DataFrame = st.session_state['mutations']
    resi = wild['resi1'].values.tolist() + wild['resi2'].values.tolist()
    net = {}
    for i in range(1, max(resi) + 1):
        query_wild = wild[
            (wild['resi1'] == i) |
            (wild['resi2'] == i)
        ]
        query_variant = variant[
            (variant['resi1'] == i) |
            (variant['resi2'] == i)
        ]
        net[i] = query_variant['total'].sum() - query_wild['total'].sum()
    return {
        'improve': [
            x for x, y in net.items() if y < 0 and x in list(mutations.index)
        ],
        'worse': [
            x for x, y in net.items() if y > 0 and x in list(mutations.index)
        ]
    }


def plot_depth(file_name: str) -> None:
    interactions: pd.DataFrame = st.session_state[f'energy_{file_name}']
    depth: Dict[int: float] = st.session_state[f'depth_{file_name}']
    mutations: pd.DataFrame = st.session_state['mutations']
    resi = interactions['resi1'].values.tolist() + \
        interactions['resi2'].values.tolist()
    assert max(resi) == max(depth.keys())
    assert min(resi) == min(depth.keys()) == 1

    net = {}
    for i in depth.keys():
        query = interactions[
            (interactions['resi1'] == i) |
            (interactions['resi2'] == i)
            ]
        net[i] = query['total'].sum()

    tool_tips = [
        ('Position', '@position'),
        ('Depth', '@x'),
        ('Net Energy', '@y')
    ]
    plot = figure(tooltips=tool_tips)
    plot.title = 'Net Energy vs Depth for Individual Residues'
    plot.xaxis.axis_label = 'Residue Depth from Surface'
    plot.yaxis.axis_label = 'Net Interaction Energy'

    source_normal = ColumnDataSource(
        data=dict(
            x=[y for x, y in depth.items() if x not in list(mutations.index)],
            y=[y for x, y in net.items() if x not in list(mutations.index)],
            position=[
                x for x in depth.keys() if x not in list(mutations.index)
            ]
        )
    )

    normal = plot.circle(
        legend_label='Conserved',
    )
    normal.data_source = source_normal
    normal.glyph.size = 6

    if file_name == 'wild':
        source_mutated = ColumnDataSource(
            data=dict(
                x=[y for x, y in depth.items() if x in list(mutations.index)],
                y=[y for x, y in net.items() if x in list(mutations.index)],
                position=[
                    x for x in depth.keys() if x in list(mutations.index)
                ]
            )
        )
        mutated = plot.circle(
            legend_label='Mutated',
            color='orange'
        )
        mutated.data_source = source_mutated
        mutated.glyph.size = 6
    elif file_name == 'variant':
        results = changes()
        source_improve = ColumnDataSource(
            data=dict(
                x=[y for x, y in depth.items() if x in results['improve']],
                y=[y for x, y in net.items() if x in results['improve']],
                position=[x for x in depth.keys() if x in results['improve']]
            )
        )
        improve = plot.circle(
            legend_label='Improvement',
            color='green'
        )
        improve.data_source = source_improve
        improve.glyph.size = 6

        source_worse = ColumnDataSource(
            data=dict(
                x=[y for x, y in depth.items() if x in results['worse']],
                y=[y for x, y in net.items() if x in results['worse']],
                position=[x for x in depth.keys() if x in results['worse']]
            )
        )
        worse = plot.circle(
            legend_label='Worse Energy',
            color='red'
        )
        worse.data_source = source_worse
        worse.glyph.size = 6

    plot.legend.location = 'top_right'
    plot.legend.click_policy = 'hide'
    st.bokeh_chart(plot, use_container_width=True)


def main():
    st.title('Residue Depth in the Protein')
    st.subheader('Wild-Type Structure')
    if check_files('wild'):
        plot_depth('wild')
    else:
        st.error('Not all Pre-requisites are calculated')

    st.subheader('Variant Structure')
    if check_files('variant'):
        plot_depth('variant')
    else:
        st.error('Not all Pre-requisites are calculated')


if __name__ == '__main__':
    main()
