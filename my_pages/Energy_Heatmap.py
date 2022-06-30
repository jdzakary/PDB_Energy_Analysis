import streamlit as st
import pandas as pd
import numpy as np
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import LinearColorMapper, ColorBar, DataTable, TableColumn
from bokeh.transform import transform
from bokeh.models.tools import WheelZoomTool, ResetTool, PanTool, TapTool
from bokeh.layouts import gridplot
import colorcet as cc

ROWS = [
    'fa_atr', 'fa_rep', 'fa_sol', 'fa_intra_rep', 'fa_intra_rep_xover4',
    'lk_ball_wtd', 'fa_elec', 'pro_close', 'hbond_sr_bb', 'hbond_lr_bb',
    'hbond_bb_sc', 'hbond_sc', 'dslf_fa13', 'omega', 'fa_dun', 'p_aa_pp',
    'yhh_planarity', 'ref', 'rama_prepro', 'total'
]


def check_files() -> bool:
    constraints = [
        'energy_wild' in st.session_state.keys(),
        'energy_variant' in st.session_state.keys()
    ]
    return all(constraints)


def fill_holes(
    data: pd.DataFrame,
    column_1: str,
    column_2: str,
    value: str
) -> pd.DataFrame:
    pivot = pd.pivot_table(data, value, column_1, column_2, np.sum)
    pivot.fillna(value=0, inplace=True)
    pivot.reset_index(level=0, inplace=True)
    return pivot.melt(id_vars=column_1, var_name=column_2, value_name=value)


def create_heatmap(file_name: str) -> dict:
    # Fetch Data
    data: pd.DataFrame = st.session_state[f'energy_{file_name}']

    # Setup Bokeh Plot
    reset = ResetTool()
    wheel_zoom = WheelZoomTool()
    pan_tool = PanTool()
    tap_tool = TapTool()
    tool_tips = [
        ('Resi1', '@x'),
        ('Resi2', '@y'),
        ('Total Energy', '@energy{0.000}')
    ]
    plot = figure(
        tools=[reset, wheel_zoom, pan_tool, tap_tool],
        tooltips=tool_tips
    )
    plot.title = f'Interaction Energy Pairs for {file_name.capitalize()}'
    plot.xaxis.axis_label = 'Position 1'
    plot.yaxis.axis_label = 'Position 2'
    plot.title.align = 'center'
    plot.title.text_font_size = '25px'

    # Create Data Source
    source = ColumnDataSource(
        data=dict(
            x=data['resi1'].values.tolist(),
            y=data['resi2'].values.tolist(),
            energy=data['total'].values.tolist()
        )
    )

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
        fill_color=transform('energy', mapper),
        line_color=None
    )

    # Final Plot Configuration
    color_bar = ColorBar(color_mapper=mapper)
    plot.add_layout(color_bar, 'right')
    plot.toolbar.active_scroll = wheel_zoom
    return {
        'plot': plot
    }


def plot_master() -> None:
    # Create Heatmaps
    wild = create_heatmap('wild')
    variant = create_heatmap('variant')
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
