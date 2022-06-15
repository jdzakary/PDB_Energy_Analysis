import json
import pandas as pd
from typing import List, Dict, Tuple, Hashable
from streamlit.uploaded_file_manager import UploadedFile


def load_interactions(
    energy_variant: UploadedFile,
    energy_wild: UploadedFile,
    mutations: UploadedFile
) -> Dict[str, pd.DataFrame]:
    variant = pd.read_csv(energy_variant)
    wild_type = pd.read_csv(energy_wild)
    mutations = pd.read_csv(mutations)

    variant.drop(variant[variant['resi2'] == '--'].index, inplace=True)
    wild_type.drop(wild_type[wild_type['resi2'] == '--'].index, inplace=True)
    variant['resi2'] = variant['resi2'].astype(int)
    wild_type['resi2'] = wild_type['resi2'].astype(int)

    mutations.sort_values(by='Position', inplace=True)
    mutations.set_index(keys='Position', inplace=True)
    return {
        'variant': variant,
        'wild_type': wild_type,
        'mutations': mutations
    }


def load_depth(file: UploadedFile) -> Dict[int, float]:
    depth = json.load(file)
    return {int(x): y for x, y in depth.items()}


def energy_calc(
    variant: pd.DataFrame,
    wild_type: pd.DataFrame,
    mutations: pd.DataFrame,
) -> Dict[str, pd.DataFrame or Dict[str, pd.DataFrame]]:

    results = interaction_analysis(variant, wild_type, mutations.index.tolist())
    salt_changes = interaction_analysis(
        salt_bridges(variant),
        salt_bridges(wild_type),
        mutations.index.tolist()
    )
    sulfide_changes = interaction_analysis(
        sulfide_bonds(variant),
        sulfide_bonds(wild_type),
        mutations.index.tolist()
    )
    hbonds_v = hydrogen_bonds(variant)
    hbonds_w = hydrogen_bonds(wild_type)
    hbonds_sc_sc = interaction_analysis(
        hbonds_v['sc_sc'],
        hbonds_w['sc_sc'],
        mutations.index.tolist()
    )
    hbonds_bb_sc = interaction_analysis(
        hbonds_v['bb_sc'],
        hbonds_w['bb_sc'],
        mutations.index.tolist()
    )
    hbonds_bb_bb_sr = interaction_analysis(
        hbonds_v['bb_bb_sr'],
        hbonds_w['bb_bb_sr'],
        mutations.index.tolist()
    )
    hbonds_bb_bb_lr = interaction_analysis(
        hbonds_v['bb_bb_lr'],
        hbonds_w['bb_bb_lr'],
        mutations.index.tolist()
    )
    data = [
        {x.upper(): len(y) for x, y in results.items()},
        {x.upper(): round(y['total'].sum(), 4) for x, y in results.items()},
        {x.upper(): len(y[y['total'] >= 1]) for x, y in results.items()},
        {x.upper(): len(y[y['total'] <= -1]) for x, y in results.items()},
        {x.upper(): len(y) for x, y in salt_changes.items()},
        {x.upper(): len(y) for x, y in sulfide_changes.items()},
        {x.upper(): len(y) for x, y in hbonds_sc_sc.items()},
        {x.upper(): len(y) for x, y in hbonds_bb_sc.items()},
        {x.upper(): len(y) for x, y in hbonds_bb_bb_sr.items()},
        {x.upper(): len(y) for x, y in hbonds_bb_bb_lr.items()}
    ]
    data = pd.DataFrame(data)
    data.index = [
        'Changes',
        'Sum',
        'Energy > 1',
        'Energy < -1',
        'Salt Bridge',
        'Sulfide Bonds',
        'SC-SC HBonds',
        'BB-SC HBonds',
        'BB-BB-SR HBonds',
        'BB-BB-LR HBonds'
    ]

    return {
        'summary': data,
        'all_changes': results,
        'salt_changes': salt_changes,
        'sulfide_changes': sulfide_changes,
        'hbonds_sc_sc': hbonds_sc_sc,
        'hbonds_bb_sc': hbonds_bb_sc,
        'hbonds_bb_bb_sr': hbonds_bb_bb_sr,
        'hbonds_bb_bb_lr': hbonds_bb_bb_lr
    }


def net_energy(
    energy_variant: UploadedFile,
    energy_wild: UploadedFile
) -> float:
    variant = pd.read_csv(energy_variant)
    wild_type = pd.read_csv(energy_wild)
    total_diff = variant["total"].sum() - wild_type["total"].sum()
    return total_diff


def salt_bridges(interactions: pd.DataFrame) -> pd.DataFrame:
    query = interactions[
        (interactions['hbond_sc'] < 0) &
        (
            (
                (interactions['restype1'].isin(['ASP', 'GLU'])) &
                (interactions['restype2'].isin(['ARG', 'HIS', 'LYS']))
            ) |
            (
                (interactions['restype1'].isin(['ARG', 'HIS', 'LYS'])) &
                (interactions['restype2'].isin(['ASP', 'GLU']))
            )
        )
    ]
    return query


def sulfide_bonds(interactions: pd.DataFrame) -> pd.DataFrame:
    query = interactions[
        (
            (interactions['restype1'] == 'CYS') &
            (interactions['restype2'] == 'CYS')
        ) |
        (interactions['dslf_fa13'] < 0)
    ]
    return query


def hydrogen_bonds(interactions: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    sc_sc = interactions[interactions['hbond_sc'] < 0]
    bb_sc = interactions[interactions['hbond_bb_sc'] < 0]
    bb_bb_sr = interactions[interactions['hbond_sr_bb'] < 0]
    bb_bb_lr = interactions[interactions['hbond_lr_bb'] < 0]
    return {
        'sc_sc': sc_sc,
        'bb_sc': bb_sc,
        'bb_bb_sr': bb_bb_sr,
        'bb_bb_lr': bb_bb_lr
    }


def interaction_analysis(
    variant: pd.DataFrame,
    wild_type: pd.DataFrame,
    mutated: List[int]
) -> Dict[str, pd.DataFrame]:
    position = ['resi1', 'resi2']

    position_v = variant[position].values.tolist()
    position_w = wild_type[position].values.tolist()

    change_a = []
    change_b = []
    change_c = []
    change_d = []
    change_e = []
    change_f = []

    for row in variant.iterrows():
        if (
            row[1][position].values.tolist() in position_w and
            (
                row[1]['resi1'] not in mutated and
                row[1]['resi2'] not in mutated
            )
        ):
            change_a.append(subtract_rows(row, wild_type))

        if (
            row[1][position].values.tolist() in position_w and
            (
                row[1]['resi1'] in mutated or
                row[1]['resi2'] in mutated
            )
        ):
            change_b.append(subtract_rows(row, wild_type))

        if (
            row[1][position].values.tolist() not in position_w and
            (
                row[1]['resi1'] not in mutated and
                row[1]['resi2'] not in mutated
            )
        ):
            change_e.append(row[1].values)

        if (
            row[1][position].values.tolist() not in position_w and
            (
                row[1]['resi1'] in mutated or
                row[1]['resi2'] in mutated
            )
        ):
            change_f.append(row[1].values)

    for row in wild_type.iterrows():
        if (
            row[1][position].values.tolist() not in position_v and
            (
                row[1]['resi1'] not in mutated and
                row[1]['resi2'] not in mutated
            )
        ):
            change_c.append(row[1].values)

        if (
            row[1][position].values.tolist() not in position_v and
            (
                row[1]['resi1'] in mutated or
                row[1]['resi2'] in mutated
            )
        ):
            change_d.append(row[1].values)

    change_a = pd.DataFrame(change_a)
    change_b = pd.DataFrame(change_b)
    change_c = pd.DataFrame(change_c)
    change_d = pd.DataFrame(change_d)
    change_e = pd.DataFrame(change_e)
    change_f = pd.DataFrame(change_f)
    dfs = [change_a, change_b, change_c, change_d, change_e, change_f]
    for i in dfs:
        if len(i) > 0:
            i.columns = variant.columns

    return {
        'a': change_a,
        'b': change_b,
        'c': change_c,
        'd': change_d,
        'e': change_e,
        'f': change_f
    }


def subtract_rows(
    row: Tuple[Hashable, pd.Series],
    df: pd.DataFrame
) -> list:
    query = df[
        (df['resi1'] == row[1]['resi1']) &
        (df['resi2'] == row[1]['resi2'])
    ].values
    data = list(row[1][0:6].values)
    data.extend(list(row[1][6:] - query[0, 6:]))
    return data


def buried_hbonds(
    residue_depth: UploadedFile,
    threshold: float,
    hbonds_sc_sc: Dict[str, pd.DataFrame],
    hbonds_bb_sc: Dict[str, pd.DataFrame],
    hbonds_bb_bb_lr: Dict[str, pd.DataFrame],
    hbonds_bb_bb_sr: Dict[str, pd.DataFrame],
    unsatisfied: bool = True,
    **kwargs
) -> None:
    data = load_depth(residue_depth)

    frames = {
        f'sc_sc_{"c" if unsatisfied else "e"}': hbonds_sc_sc['c' if unsatisfied else 'e'],
        f'sc_sc_{"d" if unsatisfied else "f"}': hbonds_sc_sc['d' if unsatisfied else 'f'],
        f'bb_sc_{"c" if unsatisfied else "e"}': hbonds_bb_sc['c' if unsatisfied else 'e'],
        f'bb_sc_{"d" if unsatisfied else "f"}': hbonds_bb_sc['d' if unsatisfied else 'f'],
        f'bb_bb_sr_{"c" if unsatisfied else "e"}': hbonds_bb_bb_sr['c' if unsatisfied else 'e'],
        f'bb_bb_sr_{"d" if unsatisfied else "f"}': hbonds_bb_bb_sr['d' if unsatisfied else 'f'],
        f'bb_bb_lr_{"c" if unsatisfied else "e"}': hbonds_bb_bb_lr['c' if unsatisfied else 'e'],
        f'bb_bb_lr_{"d" if unsatisfied else "f"}': hbonds_bb_bb_lr['d' if unsatisfied else 'f']
    }

    for key, df in frames.items():
        for row in df.iterrows():
            data_1 = data[row[1]['resi1']]
            data_2 = data[row[1]['resi2']]
            if data_1 > threshold or data_2 > threshold:
                print(f"{key:<10}", end=' ')
                print(row[1][['resi1', 'resi2', 'total']].values, end=' ')
                print(max([data_1, data_2]))
