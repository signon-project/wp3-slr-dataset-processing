import argparse
import csv
import random
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder


def stratified_grouped_split(df: pd.DataFrame) -> pd.DataFrame:
    dfc = df.copy()

    group_encoder = LabelEncoder()
    dfc['group'] = group_encoder.fit_transform(dfc.Participant.values)

    gloss_encoder = LabelEncoder()
    dfc['label'] = gloss_encoder.fit_transform(dfc.Gloss.values)

    test_ratio = 0.1  # 10% of total.
    val_ratio = 0.1111  # 11.11% of 90% -> 10% of total.

    dfc['subset'] = '?'

    random.seed(1)
    np.random.seed(1)

    cv = StratifiedGroupKFold(n_splits=int(1 / test_ratio))  # 10 splits -> 10% will be test.
    trainval_indices, test_indices = next(cv.split(dfc.Id.values, dfc.label.values, dfc.group.values))
    for index in test_indices:
        dfc.iloc[index, dfc.columns.get_loc('subset')] = 'test'

    cv = StratifiedGroupKFold(n_splits=int(1 / val_ratio))
    dfc_trainval = dfc.loc[dfc.subset == '?'].copy()
    train_indices, val_indices = next(
        cv.split(dfc_trainval.Id.values, dfc_trainval.label.values, dfc_trainval.group.values))
    for index in train_indices:
        dfc_trainval.iloc[index, dfc_trainval.columns.get_loc('subset')] = 'train'
    for index in val_indices:
        dfc_trainval.iloc[index, dfc_trainval.columns.get_loc('subset')] = 'val'

    dfc_test = dfc.loc[dfc.subset == 'test']

    dfc_complete = pd.concat([dfc_trainval, dfc_test])

    print(f'There are {len(dfc_complete.loc[dfc_complete.subset == "train"])} training samples,', end=' ')
    print(f'{len(dfc_complete.loc[dfc_complete.subset == "val"])} validation samples,', end=' ')
    print(f'and {len(dfc_complete.loc[dfc_complete.subset == "test"])} test samples.')

    assert 0 == len(dfc_complete.loc[dfc_complete.subset == "?"])

    return dfc_complete


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('csv_in', type=str, help='Input CSV file (output of create_dataset.py).')
    parser.add_argument('csv_out', type=str, help='Output CSV file.')
    parser.add_argument('glosses_out', type=str, help='Glosses output file.')

    args = parser.parse_args()

    # 1. Read CSV into DataFrame.
    df = pd.read_csv(args.csv_in)

    # 2. Perform stratified grouped dataset split.
    df = stratified_grouped_split(df)

    # 3. Drop glosses that are not present in train, val, and test.
    glosses_datasets = defaultdict(list)  # gloss -> [datasets].
    glosses = df.Gloss.unique().tolist()
    for gloss in glosses:
        rows_of_gloss = df.loc[df.Gloss == gloss]
        for subset in ['train', 'val', 'test']:
            occurs = (rows_of_gloss.subset == subset).any()
            if occurs:
                glosses_datasets[gloss].append(subset)
    glosses_in_all_subsets = list(
        map(lambda tup: tup[0], filter(lambda tup: len(tup[1]) == 3, glosses_datasets.items())))
    df = df[df.Gloss.isin(glosses_in_all_subsets)]

    # 4. Write output.
    df = df.drop(columns=['EAF', 'group', 'label'])
    df.to_csv(args.csv_out, index=False)

    with open(args.glosses_out, 'w') as of:
        writer = csv.writer(of)
        writer.writerow(['Gloss', 'Count'])
        for gloss, count in dict(df.Gloss.value_counts()).items():
            writer.writerow([gloss, count])
