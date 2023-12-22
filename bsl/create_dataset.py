import json
import random
import argparse
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


def _split_on_participant(df, rand_seed):
        unique_participants = np.unique(df.video_name.values)
        train_participants, eval_participants = train_test_split(unique_participants, test_size=0.4, random_state=rand_seed)
        val_participants, test_participants = train_test_split(eval_participants, test_size=0.5, random_state=rand_seed)
        
        train_df = df[df.video_name.isin(train_participants)].copy()
        val_df = df[df.video_name.isin(val_participants)].copy()
        test_df = df[df.video_name.isin(test_participants)].copy()
        assert len(set(train_df.video_name.unique()) & set(val_df.video_name.unique()) & set(test_df.video_name.unique())) == 0
        
        return train_df, val_df, test_df

def stratified_split(df, splits=1000):
    rand_seeds = []
    num_glosses_in_common = []
    glosses_in_common_list = []
    for i in range(splits):
        rand_seed = random.randint(1, 100000)
        rand_seeds.append(rand_seed)
        train_df, val_df, test_df = _split_on_participant(df, rand_seed)
        glosses_in_common = set(train_df.gloss.unique())&  set(val_df.gloss.unique()) &  set(test_df.gloss.unique())
        num_glosses_in_common.append(len(glosses_in_common))
        glosses_in_common_list.append(glosses_in_common)

    max_num_glosses_arg = np.argmax(num_glosses_in_common)
    max_num_glosses_seed = rand_seeds[max_num_glosses_arg]
    max_glosses_in_common = glosses_in_common_list[max_num_glosses_arg]

    train, val, test = _split_on_participant(df, max_num_glosses_seed)

    train.drop(train[~train.gloss.isin(max_glosses_in_common)].index, inplace=True)
    val.drop(val[~val.gloss.isin(max_glosses_in_common)].index, inplace=True)
    test.drop(test[~test.gloss.isin(max_glosses_in_common)].index, inplace=True)

    gloss_intersection = set(train.gloss.unique()) &  set(val.gloss.unique()) &  set(test.gloss.unique())
    gloss_union = set(train.gloss.unique()) |  set(val.gloss.unique()) |  set(test.gloss.unique())
    
    assert gloss_intersection == gloss_union
    assert set(train.gloss.unique()) ==  set(val.gloss.unique()) == set(test.gloss.unique())
    
    train['Subset'] = 'train'
    val['Subset'] = 'val'
    test['Subset'] = 'test'

    df_out = pd.concat([train, val, test])
    
    return df_out, glosses_in_common_list[max_num_glosses_arg]

def encode_labels(df):
    dfc = df.copy()

    #Original video naming convention based on participant so we can use this: 
    part_encoder = LabelEncoder()
    dfc['Participant'] = part_encoder.fit_transform(dfc.video_name.values)

    #Int labels for glosses: 
    gloss_encoder = LabelEncoder()
    dfc['Label'] = gloss_encoder.fit_transform(dfc.gloss.values)

    #Save the mapping of these gloss labels:
    gloss_mapping = dict(zip(map(int, gloss_encoder.transform(gloss_encoder.classes_)), gloss_encoder.classes_))
    with open('gloss_mapping.json', 'w') as outfile:
        json.dump(gloss_mapping, outfile)

    #Drop "gloss" column:
    dfc.drop('gloss', axis=1, inplace=True)

    return dfc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--csv_in', type=str, help='Input .csv file from clean_dataset.py step.')
    parser.add_argument('--csv_out', type=str, help='Output .csv of split dataset ready for clip extraction.')

    args = parser.parse_args()
    
    #1. Load CSV from previous step:
    step2_df = pd.read_csv(args.csv_in)

    #2. Verify this is in the right form for cleaning/processing:
    #   Form: ['video_name', 'start_ms', 'end_ms', 'gloss']
    col_names = list(step2_df)
    if not col_names == ['video_name', 'start_ms', 'end_ms', 'gloss']:
        raise Exception("CSV not in correct form. Check column values.")

    #3. Perform stratified split:
    #   Form should now be: ['video_name', 'start_ms', 'end_ms', 'gloss', 'Subset']
    _tmp, glosses = stratified_split(step2_df)

    print(f'There are {len(_tmp.loc[_tmp.Subset == "train"])} training samples,', end=' ')
    print(f'{len(_tmp.loc[_tmp.Subset == "val"])} validation samples,', end=' ')
    print(f'and {len(_tmp.loc[_tmp.Subset == "test"])} test samples.')

    print(f'There are {len(glosses)} unique glosses in the dataset.')

    #4. Encode labels: 
    #   Form will now be: ['video_name', 'start_ms', 'end_ms', 'Subset', 'Participant', 'Label']
    step3_df = encode_labels(_tmp)

    #5. Save: 
    step3_df.to_csv(args.csv_out, index=False)