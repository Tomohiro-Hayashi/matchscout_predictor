import pandas as pd
import numpy as np
import itertools
import sys
from statistics import mean,median,variance,stdev

#訓練データ,ユーザー抽出データ、どちらを前処理するのか選ぶ
args = sys.argv
if args[1] == 'train':
    ##訓練データの読み込み
    data = pd.read_csv("training/train_data.csv")
    ##マッチ度の計算に用いる会員データの読み込み
    user_pref = pd.read_csv('training/user_pref.csv')
    user_occupation = pd.read_csv('training/user_occupation.csv')
    user_exp = pd.read_csv('training/user_exp.csv')
    user_licentiate = pd.read_csv('training/user_licentiate.csv')
    ##例外処理 : この処理はクエリに書いた方が綺麗になるかもしれない
    data['annualpay'] = np.nan
    data.loc[data['salary_system'] == 'annual', 'annualpay'] = data.loc[data['salary_system'] == 'annual', 'salary']
    data.loc[data['salary_system'] == 'salary', 'annualpay'] = data.loc[data['salary_system'] == 'salary', 'salary'] * 12
    ##ローデータの統計量を書き出す
    pd.DataFrame({
        'wanted_annualpay': [data['wanted_annualpay'].mode()[0]],
        'annualpay': [data['annualpay'].mode()[0]],
        'age': [data['age'].mode()[0]],
        'age_upper': [data['age_upper'].mode()[0]]
    }).to_csv('statistics_values_mode.csv')
elif args[1] == 'test':
    ##ターゲットデータの読み込み
    user_list = pd.read_csv("target/user_list.csv")
    work_list = pd.read_csv("target/work_list.csv")
    exception = pd.read_csv("target/exception.csv")
    ##会員求人の組み合わせ抽出
    user_occupation_table = pd.read_csv("target/user_occupation_table.csv")
    user_occupation_table = pd.merge(user_list['member_id'], user_occupation_table, how = 'inner')
    work_occupation_table = pd.read_csv("target/work_occupation_table.csv")
    work_occupation_table = pd.merge(work_list['work_id'], work_occupation_table, how = 'inner')
    user_work = pd.read_csv('preprocess/occupation_vector_similarities.csv')
    user_work = user_work[user_work['similarity'] >= 0.15]
    user_work = pd.merge(user_work, user_occupation_table, left_on = 'occupation_id_a', right_on = 'occupation_id1')
    user_work = pd.merge(user_work, work_occupation_table, left_on = 'occupation_id_b', right_on = 'occupation_id2')
    user_work = user_work[['member_id', 'work_id']].drop_duplicates()
    ##ターゲットデータの作成
    data = pd.merge(user_work, user_list)
    data = pd.merge(data, work_list)
    data = data[~(data['member_id'].isin(exception['member_id']) & data['company_id'].isin(exception['company_id']))]
    ##テスト実行のため,一部だけランダム抽出
    data = data.sample(frac=0.01)
    ##マッチ度の計算に用いる会員データの読み込み
    user_pref = pd.read_csv('target/user_pref.csv')
    user_occupation = pd.read_csv('target/user_occupation_table.csv')
    user_exp = pd.read_csv('target/user_exp.csv')
    user_licentiate = pd.read_csv('target/user_licentiate.csv')
    ##例外処理 : この処理もクエリに書いて、こちらは消した方が良いかも
    data['annualpay'] = np.nan
    data.loc[data['salary_system'] == 'annual', 'annualpay'] = data.loc[data['salary_system'] == 'annual', 'salary']
    data.loc[data['salary_system'] == 'salary', 'annualpay'] = data.loc[data['salary_system'] == 'salary', 'salary'] * 12
##前処理に用いる統計量の読み込み
mode = pd.read_csv('preprocess/statistics_values_mode.csv')
##マッチ度の計算に用いる求人データの読み込み
work_pref = pd.read_csv('preprocess/work_pref.csv')
work_occupation = pd.read_csv('preprocess/work_occupation.csv')
work_exp = pd.read_csv('preprocess/work_exp.csv')
work_licentiate = pd.read_csv('preprocess/work_licentiate.csv')
##マッチ度の計算に用いる類似度のデータの読み込み
pref_similarity = pd.read_csv('preprocess/pref_entry_rate_作成コード/pref_entry_rate.csv')
occupation_similarity = pd.read_csv('preprocess/occupation_vector_similarities.csv')
exp_similarity_converter = pd.read_csv('preprocess/exp_similarity_作成コード/exp_similarity.csv')
licentiate_similarity_converter = pd.read_csv('preprocess/licentiate_similarity_作成コード/licentiate_similarity.csv')

####ローデータの処理####
##①例外処理
##wanted_annualpay
data['wanted_annualpay'] = data['wanted_annualpay'].astype('str')
f = lambda x :x.split('～')[0]
data['wanted_annualpay'] = data['wanted_annualpay'].apply(f)
data['wanted_annualpay'] = data['wanted_annualpay'].replace('', str(151)).replace('nan',str(0))
data['wanted_annualpay'] = data['wanted_annualpay'].astype(int)

##欠損値補完
defect_value = {
    'age': mode.age[0],
    'age_upper': 65,
    'wanted_annualpay': mode.wanted_annualpay[0],
    'annualpay': mode.annualpay[0],
}
for col_name in defect_value:
    data[col_name] = data[col_name].fillna(defect_value[col_name])

##外れ値補完
for key in ['age','age_upper']:
    data.loc[data[key] >= 90, key] = 90
    data.loc[data[key] <= 0, key] = 15
data.loc[data['annualpay'] >= 1500, 'annualpay'] = 1500
data.loc[data['annualpay'] <= 0, 'annualpay'] = 150

####マッチ度の作成####
##pref_match
index_list = pd.DataFrame({'user_pref_id' : [ n for n in range(1,48) for m in range(1,48) ], 'work_pref_id' : [ m for n in range(1,48) for m in range(1,48) ]})
pref_similarity = pd.merge(index_list, pref_similarity, on = ['user_pref_id','work_pref_id'])
pref_match = pd.merge(data, work_pref[['work_id', 'work_pref_id']], on = 'work_id')
pref_match = pd.merge(pref_match, user_pref[['member_id', 'user_pref_id']], on = 'member_id')
pref_similarity['user_pref_id'] = pref_similarity['user_pref_id'].astype(str)
pref_similarity['work_pref_id'] = pref_similarity['work_pref_id'].astype(str)
pref_match['user_pref_id'] = pref_match['user_pref_id'].astype(str)
pref_match['work_pref_id'] = pref_match['work_pref_id'].astype(str)
pref_match = pd.merge(pref_match, pref_similarity, on = ['work_pref_id', 'user_pref_id'])
pref_match['pref_match'] = pref_match['entry_rate']
pref_match = pref_match[['member_id', 'work_id', 'pref_match']].loc[pref_match.groupby(['member_id', 'work_id'])['pref_match'].idxmax()]
data = pd.merge(data, pref_match[['member_id', 'work_id', 'pref_match']], on = ['member_id', 'work_id'], how = 'left')

##occupation_match
occupation_match = pd.merge(data, user_occupation[['member_id', 'occupation_id1']], on = 'member_id')
occupation_match = pd.merge(occupation_match, work_occupation[['work_id', 'occupation_id2']], on = 'work_id')
occupation_similarity['occupation_id_a'] = occupation_similarity['occupation_id_a'].astype(int)
occupation_similarity['occupation_id_b'] = occupation_similarity['occupation_id_b'].astype(int)
occupation_match['occupation_id1'] = occupation_match['occupation_id1'].astype(int)
occupation_match['occupation_id2'] = occupation_match['occupation_id2'].astype(int)
occupation_match = pd.merge(occupation_match, occupation_similarity, left_on = ['occupation_id1', 'occupation_id2'], right_on = ['occupation_id_a','occupation_id_b'])
occupation_match['occupation_match'] = occupation_match['similarity']
occupation_match = occupation_match[['member_id', 'work_id', 'occupation_match']].loc[occupation_match.groupby(['member_id', 'work_id'])['occupation_match'].idxmax()]
data = pd.merge(data, occupation_match[['member_id', 'work_id', 'occupation_match']], on = ['member_id', 'work_id'], how = 'left')

#exp_match
data = pd.merge(data, work_exp, on = 'work_id', how = 'left')
data = pd.merge(data, user_exp, on = 'member_id', how = 'left')
##exp_id 1~1008 に対応する exp_check_number を要素とするようなベクトルを作る
for col_name in ['work_exp_id', 'user_exp_id']:
    data[col_name] = data[col_name].fillna('0').str.split(',').replace('', '0')
    data[col_name] = [ [int(str) if str != '' else 0 for str in element] for element in data[col_name]  ]
for col_name in ['work_exp_check_number', 'user_exp_check_number']:
    data[col_name] = data[col_name].fillna('0').str.split(',').replace('', '0')
    data[col_name] = [ [float(str) if str != '' else 0 for str in element] for element in data[col_name]  ]
data['work_exp_level_vector'] = [ [ [ row.work_exp_check_number[row.work_exp_id.index(n)]][0] if n in row.work_exp_id else 0 for n in range(1,1009)] for row in data.itertuples()]
data['user_exp_level_vector'] = [ [ [ row.user_exp_check_number[row.user_exp_id.index(n)]][0] if n in row.user_exp_id else 0 for n in range(1,1009)] for row in data.itertuples()]
##exp_levelに対応する数値を下記のように決め、代入する
weight = {1: 0.5, 2: 0.7, 3: 1.0}
data['work_exp_level_vector'] = [pd.DataFrame(data['work_exp_level_vector'][n]).replace(weight).T.values.tolist()[0] for n in range(len(data))]
data['user_exp_level_vector'] = [pd.DataFrame(data['user_exp_level_vector'][n]).replace(weight).T.values.tolist()[0] for n in range(len(data))]
##類似度行列にはexp_idの欠損があるので、それを補う
index_list = pd.DataFrame({'exp_id_a' : [ n for n in range(1,1009) for m in range(1,1009)], 'exp_id_b' : [ m for n in range(1,1009) for m in range(1,1009)]})
exp_similarity_converter = pd.merge(index_list, exp_similarity_converter, on = ['exp_id_a', 'exp_id_b'], how = 'left').fillna(0)
##クロス集計して縦横がexp_idに対応するようにする
tally = pd.pivot_table(exp_similarity_converter, values='similarity', index='exp_id_a', columns='exp_id_b')
##exp_level_vectorにこの類似度行列を作用させ、ひとつのexp_idに紐つく複数の類似exp_idに成分を持たせる
data['work_exp_level_vector'] = [np.dot(tally, row.work_exp_level_vector) for row in data.itertuples()]
##exp_level_vectorの全成分が0のケースだけ例外処理する
data['work_exp_level_vector_len'] = [np.linalg.norm(row.work_exp_level_vector, ord=2) for row in data.itertuples()]
data['work_exp_level_vector'] = [pd.DataFrame(data['work_exp_level_vector'][n]).replace({0.0:0.05}).T.values.tolist()[0] if data['work_exp_level_vector_len'][n] == 0.0 else data['work_exp_level_vector'][n] for n in range(len(data))]
##exp_level_vectorとuser_exp_level_vectorのベクトル類似度を計算する
data['exp_match'] = [np.dot(row.work_exp_level_vector, row.user_exp_level_vector) *1.0 /max( np.linalg.norm(row.work_exp_level_vector, ord=2) * np.linalg.norm(row.user_exp_level_vector, ord=2), 1 ) for row in data.itertuples()]
data = data.drop(['work_exp_id', 'work_exp_check_number', 'user_exp_id', 'user_exp_check_number', 'work_exp_level_vector', 'user_exp_level_vector'], axis=1)

##licentiate_match
data = pd.merge(data, work_licentiate, on = 'work_id')
data = pd.merge(data, user_licentiate, on = 'member_id')
##licentiate_id 1~2069 に対応する ベクトルを作る : 01はidの登録有無に対応する
for col_name in ['work_licentiate_id', 'user_licentiate_id']:
    data[col_name] = data[col_name].fillna('0').str.split(',').replace('', '0')
    data[col_name] = [ [int(str) if str != '' else 0 for str in element] for element in data[col_name]  ]
data['work_licentiate_vector'] = [ [ 1 if n in row.work_licentiate_id else 0 for n in range(1, 2070) ] for row in data.itertuples()]
data['user_licentiate_vector'] = [ [ 1 if n in row.user_licentiate_id else 0 for n in range(1, 2070) ] for row in data.itertuples()]
##類似度行列にはexp_idの欠損があるので、それを補う
index_list = pd.DataFrame({'licentiate_id_a' : [ n for n in range(1, 2070) for m in range(1, 2070)], 'licentiate_id_b' : [ m for n in range(1, 2070) for m in range(1,2070)]})
licentiate_similarity_converter = pd.merge(index_list, licentiate_similarity_converter, on = ['licentiate_id_a', 'licentiate_id_b'], how = 'left').fillna(0)
licentiate_similarity_converter.loc[(licentiate_similarity_converter.licentiate_id_b == licentiate_similarity_converter.licentiate_id_a), 'similarity'] = 1.0
##クロス集計して縦横がexp_idに対応するようにする
tally = pd.pivot_table(licentiate_similarity_converter, values='similarity', index='licentiate_id_a', columns='licentiate_id_b')
##licentiate_vectorにこの類似度行列を作用させ、ひとつの#licentiate_idに紐つく複数の類似#licentiate_idに成分を持たせる
data['work_licentiate_vector'] = [np.dot(row.work_licentiate_vector, tally) for row in data.itertuples()]
##licentiate_vectorの全成分が0のケースだけ例外処理する
data['work_licentiate_vector_len'] = [np.linalg.norm(row.work_licentiate_vector, ord=2) for row in data.itertuples()]
data['work_licentiate_vector'] = [pd.DataFrame(data['work_licentiate_vector'][n]).replace({0.0:0.01}).T.values.tolist()[0] if data['work_licentiate_vector_len'][n] == 0.0 else data['work_licentiate_vector'][n] for n in range(len(data))]
data['licentiate_match'] = [np.dot(row.work_licentiate_vector, row.user_licentiate_vector) *1.0 /max( np.linalg.norm(row.work_licentiate_vector, ord=2) * np.linalg.norm(row.user_licentiate_vector, ord=2), 1) for row in data.itertuples()]
data = data.drop(['work_licentiate_id', 'user_licentiate_id', 'work_licentiate_vector', 'user_licentiate_vector'], axis=1)

##gender_match
data['gender_match'] = 0
data.loc[data['work_gender'] == 'both', 'gender_match'] = 1
data.loc[data['work_gender'] ==  data['user_gender'], 'gender_match'] = 1
data.loc[(data['work_gender'].isna()), 'gender_match'] = 1

##annualpay_match
data['annualpay_match'] = data['annualpay'] - data['wanted_annualpay']

##age_match
data['age_match'] = data['age_upper'] - data['age']

if args[1] == 'train':
    statistics_values = pd.DataFrame({
        'annualpay_match_mean': [data['annualpay_match'].mean()],
        'annualpay_match_stdev': [stdev(data['annualpay_match'])],
        'age_match_mean': [data['age_match'].mean()],
        'age_match_stdev': [stdev(data['age_match'])],
        'pref_match': [data['pref_match'].mode()[0]],
        'occupation_match': [0],
        'exp_match': [0],
        'licentiate_match': [0],
    })
    statistics_values.to_csv('preprocess/statistics_values.csv')
elif args[1] == 'test':
    statistics_values = pd.read_csv("preprocess/statistics_values.csv")

##欠陥値処理
for match_degree in ['pref_match','occupation_match','exp_match','licentiate_match']:
    data[match_degree] = data[match_degree].fillna(statistics_values[match_degree][0])

##正規化
data['annualpay_match'] = (data['annualpay_match'] - statistics_values['annualpay_match_mean'][0])/statistics_values['annualpay_match_stdev'][0]
data['age_match'] = (data['age_match'] -statistics_values['age_match_mean'][0])/statistics_values['age_match_stdev'][0]

if args[1] == 'train':
    data = data[
        [
            'member_id',
            'work_id',
            'age_match',
            'annualpay_match',
            'pref_match',
            'occupation_match',
            'exp_match',
            'licentiate_match',
            'gender_match',
            'entry_flg'
        ]
    ]
    data.to_csv("preprocess/preprocess.csv", index = False)
elif args[1] == 'test':
    data = data[
        [
            'member_id',
            'work_id',
            'age_match',
            'annualpay_match',
            'pref_match',
            'occupation_match',
            'exp_match',
            'licentiate_match',
            'gender_match'
        ]
    ]
    data.to_csv("preprocess/preprocess_target.csv", index = False)
