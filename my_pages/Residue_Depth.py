import pandas as pd
import streamlit as st
from typing import Dict, List
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import CustomJS, DataTable, TableColumn
from bokeh.layouts import column


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
    # Fetch Data from Streamlit Session State
    inter: pd.DataFrame = st.session_state[f'energy_{file_name}']
    depth: Dict[int: float] = st.session_state[f'depth_{file_name}']
    if 'mutations' in st.session_state.keys():
        mutations: pd.DataFrame = st.session_state['mutations']
        mut_list = list(mutations.index)
    else:
        mut_list = []
    resi = inter['resi1'].values.tolist() + inter['resi2'].values.tolist()
    assert max(resi) == max(depth.keys())
    assert min(resi) == min(depth.keys()) == 1

    # Calculate Net Energy Changes
    entries = {}
    net = {}
    for i in depth.keys():
        query = inter[(inter['resi1'] == i) | (inter['resi2'] == i)]
        net[i] = query['total'].sum()
        entries[i] = query[['resi1', 'resi2', 'total']].values.tolist()

    # Setup Bokeh Plot
    tool_tips = [
        ('Position', '@position'),
        ('Depth', '@x'),
        ('Net Energy', '@y')
    ]
    plot = figure(
        tools="reset,pan,wheel_zoom,tap",
        tooltips=tool_tips
    )
    plot.title = 'Net Energy vs Depth for Individual Residues'
    plot.xaxis.axis_label = 'Residue Depth from Surface'
    plot.yaxis.axis_label = 'Net Interaction Energy'

    # Create Data Sources
    sources = {
        'normal': ColumnDataSource(
            data=dict(
                x=[y for x, y in depth.items() if x not in mut_list],
                y=[y for x, y in net.items() if x not in mut_list],
                position=[x for x in depth.keys() if x not in mut_list]
            )
        )
    }
    normal = plot.circle(legend_label='Conserved')
    normal.data_source = sources['normal']
    normal.glyph.size = 6

    # Create Additional Data Sources
    if file_name == 'wild':
        sources['mutated'] = ColumnDataSource(
            data=dict(
                x=[y for x, y in depth.items() if x in mut_list],
                y=[y for x, y in net.items() if x in mut_list],
                position=[x for x in depth.keys() if x in mut_list]
            )
        )
        mutated = plot.circle(
            legend_label='Mutated',
            color='orange'
        )
        mutated.data_source = sources['mutated']
        mutated.glyph.size = 6
    elif file_name == 'variant':
        results = changes()
        sources['improve'] = ColumnDataSource(
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
        improve.data_source = sources['improve']
        improve.glyph.size = 6

        sources['worse'] = ColumnDataSource(
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
        worse.data_source = sources['worse']
        worse.glyph.size = 6

    # Setup Bokeh Table
    source_master = ColumnDataSource(inter[['resi1', 'resi2', 'total']])
    source_copy = ColumnDataSource(
        data=dict(resi1=[], resi2=[], total=[])
    )
    table = DataTable(
        source=source_copy,
        columns=[
            TableColumn(field='resi1', title='Position 1'),
            TableColumn(field='resi2', title='Position 2'),
            TableColumn(field='total', title='Total Score')
        ]
    )

    # Setup JavaScript
    for i in sources.values():
        i.selected.js_on_change(
            'indices',
            CustomJS(
                args=dict(
                    source=i,
                    entries=entries,
                    sm=source_master,
                    sc=source_copy
                ),
                code="""
                var select = source.selected.indices;
                const smd = sm.data;
                const scd = sc.data;
                if (select.length == 1) {
                    var j = source.data['position'][select[0]];
                    scd['resi1'] = [];
                    scd['resi2'] = [];
                    scd['total'] = [];
                    for (const i of entries[j]) {
                        scd['resi1'].push(i[0]);
                        scd['resi2'].push(i[1]);
                        scd['total'].push(i[2]);
                    }
                    sc.change.emit();
                }
                """
            )
        )
    # Final Configuration and show Plot
    plot.legend.location = 'top_right'
    plot.legend.click_policy = 'hide'
    st.bokeh_chart(column(plot, table), use_container_width=True)


def main():
    st.title('Residue Depth in the Protein')
    col1, col2 = st.columns(2)
    col1.subheader('Wild-Type Structure')
    if check_files('wild'):
        with col1:
            plot_depth('wild')
    else:
        col1.error('Not all Pre-requisites are calculated')

    col2.subheader('Variant Structure')
    if check_files('variant'):
        with col2:
            plot_depth('variant')
    else:
        col2.error('Not all Pre-requisites are calculated')


if __name__ == '__main__':
    main()
