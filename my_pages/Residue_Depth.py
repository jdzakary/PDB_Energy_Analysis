import pandas as pd
import streamlit as st
from typing import Dict
from bokeh.plotting import figure, ColumnDataSource, Figure
from bokeh.models import CustomJS, DataTable, TableColumn
from bokeh.models.tools import WheelZoomTool, ResetTool, PanTool, TapTool
from bokeh.layouts import gridplot


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


def changes() -> Dict[int, int]:
    wild: pd.DataFrame = st.session_state['energy_wild']
    variant: pd.DataFrame = st.session_state['energy_variant']
    mutations: pd.DataFrame = st.session_state['mutations']
    resi = wild['resi1'].values.tolist() + wild['resi2'].values.tolist()
    mut_idx = list(mutations.index)
    results = {}
    for i in range(1, max(resi) + 1):
        if i not in mut_idx:
            results[i] = 0
            continue
        query_wild = wild[
            (wild['resi1'] == i) |
            (wild['resi2'] == i)
        ]
        query_variant = variant[
            (variant['resi1'] == i) |
            (variant['resi2'] == i)
        ]
        net = query_variant['total'].sum() - query_wild['total'].sum()
        results[i] = 1 if net > 0 else 2
    return results


@st.cache
def read_js(version: int) -> str:
    with open(f'js/residue_depth_{version}.js', 'r') as file:
        return file.read()


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
    reset = ResetTool()
    wheel_zoom = WheelZoomTool()
    pan_tool = PanTool()
    tap_tool = TapTool()
    tool_tips = [
        ('Position', '@position'),
        ('Depth', '@x'),
        ('Net Energy', '@y')
    ]
    plot = figure(
        tools=[reset, wheel_zoom, pan_tool, tap_tool],
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
    normal = plot.circle(
        legend_label='Conserved',
        source=sources['normal'],
        nonselection_alpha=0
    )
    #normal.data_source = sources['normal']
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
    plot.toolbar.active_scroll = wheel_zoom


def create_source_wild(
    depth: Dict[int, float],
    net: Dict[int, float],
    mut_map: Dict[int, int]
) -> ColumnDataSource:
    c1 = (9, 92, 224, 1)
    c2 = (224, 138, 9)
    mut_list = [x != 0 for x in mut_map.values()]
    source = ColumnDataSource(
        data=dict(
            x=list(depth.values()),
            y=list(net.values()),
            position=list(depth.keys()),
            color=[c2 if x else c1 for x in mut_list],
            label=['Mutated' if x else 'Conserved' for x in mut_list]
        )
    )
    return source


def create_source_variant(
    depth: Dict[int, float],
    net: Dict[int, float],
    mut_map: Dict[int, int]
) -> ColumnDataSource:
    color_map = [(9, 92, 224), (230, 9, 9), (69, 214, 95)]
    label_map = ['Conserved', 'Worse Energy', 'Better Energy']
    source = ColumnDataSource(
        data=dict(
            x=list(depth.values()),
            y=list(net.values()),
            position=list(depth.keys()),
            color=[color_map[x] for x in mut_map.values()],
            label=[label_map[x] for x in mut_map.values()]
        )
    )
    return source


def create_plot(file_name: str) -> (
    ColumnDataSource, Figure, DataTable,
    ColumnDataSource, Dict[int, list]
):
    # Fetch Data from Streamlit Session State
    inter: pd.DataFrame = st.session_state[f'energy_{file_name}']
    depth: Dict[int: float] = st.session_state[f'depth_{file_name}']
    mut_map = changes()
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
    reset = ResetTool()
    wheel_zoom = WheelZoomTool()
    pan_tool = PanTool()
    tap_tool = TapTool()
    tool_tips = [
        ('Position', '@position'),
        ('Depth', '@x'),
        ('Net Energy', '@y')
    ]
    plot = figure(
        tools=[reset, wheel_zoom, pan_tool, tap_tool],
        tooltips=tool_tips
    )
    plot.title = f'{file_name.capitalize()}: Net Energy vs Depth'
    plot.xaxis.axis_label = 'Residue Depth from Surface'
    plot.yaxis.axis_label = 'Net Interaction Energy'

    # Create Data Source
    if file_name == 'wild':
        source = create_source_wild(depth, net, mut_map)
    else:
        source = create_source_variant(depth, net, mut_map)
    plot.circle(
        source=source,
        legend_group='label',
        color='color',
        radius=0.05
    )

    # Setup Bokeh Table
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

    # Final Plot Configuration
    plot.legend.location = 'top_right'
    plot.toolbar.active_scroll = wheel_zoom
    return plot, source, table, source_copy, entries


def plot_master() -> None:
    w_p, w_s, w_t, w_sc, w_e = create_plot('wild')
    v_p, v_s, v_t, v_sc, v_e = create_plot('variant')
    var_maps = dict(
        wild=dict(
            source=w_s, s_e=w_e, sc=w_sc, oc=v_sc, o_e=v_e, o_s=v_s
        ),
        variant=dict(
            source=v_s, s_e=v_e, sc=v_sc, oc=w_sc, o_e=w_e, o_s=w_s
        )
    )

    for item in var_maps.values():
        item['source'].selected.js_on_change(
            'indices',
            CustomJS(
                args={**item},
                code=read_js(1)
            )
        )
    st.bokeh_chart(
        gridplot([
            [w_p, v_p],
            [w_t, v_t]
        ]),
        use_container_width=False
    )


def main():
    st.title('Residue Depth in the Protein')
    if check_files('wild') and check_files('variant'):
        plot_master()
    else:
        st.error('Not all Pre-requisites are calculated')


if __name__ == '__main__':
    main()
