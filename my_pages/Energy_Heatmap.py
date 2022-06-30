import streamlit as st
import pandas as pd
import numpy as np
import colorcet as cc
from typing import Dict
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import LinearColorMapper, ColorBar, DataTable, TableColumn
from bokeh.transform import transform
from bokeh.models.tools import (
    WheelZoomTool, ResetTool, PanTool, TapTool, BoxSelectTool
)
from bokeh.models.callbacks import CustomJS
from bokeh.layouts import gridplot


ROWS = [
    'fa_atr', 'fa_rep', 'fa_sol', 'fa_intra_rep', 'fa_intra_sol_xover4',
    'lk_ball_wtd', 'fa_elec', 'pro_close', 'hbond_sr_bb', 'hbond_lr_bb',
    'hbond_bb_sc', 'hbond_sc', 'dslf_fa13', 'omega', 'fa_dun', 'p_aa_pp',
    'yhh_planarity', 'ref', 'rama_prepro', 'total'
]


def read_js(version: int) -> str:
    with open(f'js/energy_heatmap_{version}.js', 'r') as file:
        return file.read()


def check_files() -> bool:
    constraints = [
        'energy_wild' in st.session_state.keys(),
        'energy_variant' in st.session_state.keys()
    ]
    return all(constraints)


def cool_stuff(
    data: pd.DataFrame,
    column_1: str,
    column_2: str,
    value: str
) -> pd.DataFrame:
    pivot = pd.pivot_table(data, value, column_1, column_2, np.sum)
    pivot.fillna(value=0, inplace=True)
    pivot.reset_index(level=0, inplace=True)
    return pivot.melt(id_vars=column_1, var_name=column_2, value_name=value)


def fill_holes() -> Dict[str, pd.DataFrame]:
    wild = st.session_state['energy_wild']
    variant = st.session_state['energy_variant']
    cw = pd.DataFrame(wild[ROWS + ['resi1', 'resi2']], copy=True)
    cv = pd.DataFrame(variant[ROWS + ['resi1', 'resi2']], copy=True)
    pairs_w = cw[['resi1', 'resi2']].values.tolist()
    pairs_v = cv[['resi1', 'resi2']].values.tolist()

    new_values = []
    for resi1, resi2 in [x for x in pairs_v if x not in pairs_w]:
        row = {'resi1': resi1, 'resi2': resi2}
        row.update({x: 0 for x in ROWS})
        new_values.append(row)
    cw = pd.concat([cw, pd.DataFrame(new_values)])

    new_values = []
    for resi1, resi2 in [x for x in pairs_w if x not in pairs_v]:
        row = {'resi1': resi1, 'resi2': resi2}
        row.update({x: 0 for x in ROWS})
        new_values.append(row)
    cv = pd.concat([cv, pd.DataFrame(new_values)])

    cw.sort_values(by=['resi1', 'resi2'], inplace=True)
    cv.sort_values(by=['resi1', 'resi2'], inplace=True)
    return {'wild': cw, 'variant': cv}


def create_heatmap(
    file_name: str,
    data: pd.DataFrame
) -> dict:
    # Setup Bokeh Plot
    reset = ResetTool()
    wheel_zoom = WheelZoomTool()
    pan_tool = PanTool()
    tap_tool = TapTool()
    poly = BoxSelectTool()
    tool_tips = [
        ('Resi1', '@x'),
        ('Resi2', '@y'),
        ('Total Energy', '@total{0.000}')
    ]
    plot = figure(
        tools=[reset, wheel_zoom, pan_tool, tap_tool, poly],
        tooltips=tool_tips
    )
    plot.title = f'Interaction Energy Pairs for {file_name.capitalize()}'
    plot.xaxis.axis_label = 'Position 1'
    plot.yaxis.axis_label = 'Position 2'
    plot.title.align = 'center'
    plot.title.text_font_size = '25px'

    # Create Data Source
    source_data = {
        'x': data['resi1'].values.tolist(),
        'y': data['resi2'].values.tolist()
    }
    source_data.update({x: data[x].values.tolist() for x in ROWS})
    source = ColumnDataSource(data=source_data)

    # Create Heatmap
    mapper = LinearColorMapper(
        palette=cc.b_linear_bmy_10_95_c78,
        low=-5,
        high=5
    )
    plot.rect(
        source=source,
        width=1,
        height=1,
        fill_color=transform('total', mapper),
        line_color=None
    )

    # Final Plot Configuration
    color_bar = ColorBar(color_mapper=mapper)
    plot.add_layout(color_bar, 'right')
    plot.toolbar.active_scroll = wheel_zoom
    return {
        'plot': plot,
        'source': source
    }


def plot_master() -> None:
    # Create Heatmaps
    df = fill_holes()
    wild = create_heatmap('wild', df['wild'])
    variant = create_heatmap('variant', df['variant'])
    wild['plot'].width = 575
    variant['plot'].width = 575

    # Link Pan and Scroll
    wild['plot'].x_range = variant['plot'].x_range
    wild['plot'].y_range = variant['plot'].y_range

    # Bokeh Table
    source_table = ColumnDataSource(
        data=dict(
            energy=ROWS,
            wild=[0] * len(ROWS),
            variant=[0] * len(ROWS)
        )
    )
    table = DataTable(
        source=source_table,
        columns=[
            TableColumn(field='energy', title='Energy Term'),
            TableColumn(field='wild', title='Wild-Type'),
            TableColumn(field='variant', title='Variant'),
        ],
        index_position=None,
        width=250,
        height=535
    )

    # JS Code Linking Selections
    wild['source'].selected.js_on_change(
        'indices',
        CustomJS(
            args=dict(
                source=wild['source'],
                other=variant['source']
            ),
            code=read_js(1)
        )
    )
    variant['source'].selected.js_on_change(
        'indices',
        CustomJS(
            args=dict(
                source=variant['source'],
                other=wild['source']
            ),
            code=read_js(1)
        )
    )
    wild['source'].selected.js_on_change(
        'indices',
        CustomJS(
            args=dict(
                wild=wild['source'],
                variant=variant['source'],
                rows=ROWS,
                table=source_table
            ),
            code=read_js(2)
        )
    )

    st.bokeh_chart(
        gridplot([
            [wild['plot'], variant['plot'], table],
        ])
    )


def main():
    st.title('Energy Heatmap')
    if check_files():
        plot_master()
    else:
        st.error('Not all Pre-Requisites are Calculated')
