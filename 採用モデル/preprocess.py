import pandas as pd
import numpy as np
from statistics import mean, median, variance, stdev

#訓練データの前処理
data = pd.read_csv("training/training.csv")
data['annualpay'] = np.nan
data.loc[data['salary_system'] == 'annual', 'annualpay'] = data.loc[data['salary_system'] == 'annual', 'salary']
data.loc[data['salary_system'] == 'salary', 'annualpay'] = data.loc[data['salary_system'] == 'salary', 'salary'] * 12
mode = pd.DataFrame({
    'wanted_annualpay': [data['wanted_annualpay'].mode()[0]],
    'annualpay': [data['annualpay'].mode()[0]],
    'age': [data['age'].mode()[0]],
    'age_lower': [data['age_lower'].mode()[0]],
    'age_upper': [data['age_upper'].mode()[0]]
})
searchparameter = pd.read_csv('training/work_searchparameters.csv')
data = pd.merge(data, searchparameter, on = 'work_id', how = 'left')

##類似度行列 : マッチ度の計算に使用
exp_similarity_converter = pd.read_csv('preprocess/exp_similarity.csv')
licentiate_similarity_converter = pd.read_csv('preprocess/licentiate_similarity.csv')

##欠損値補完
defect_value = {
    'age': mode.age[0],
    'age_from': 15,
    'age_to': 65,
    'age_lower': mode.age_lower[0],
    'age_upper': mode.age_upper[0],
    'wanted_annualpay': mode.wanted_annualpay[0],
    'annualpay': mode.annualpay[0],
    'gender': 'unknown',
    'sex': '0',
    'user_exp_id': '0',
    'user_exp_check_number': '0',
    'exp_id': '0',
    'exp_check_number': '0',
    'exp_cond': 1,
    # 'user_licentiate_id': '-1',
    # 'licentiate_id': '-1',
    # 'licentiate_cond': 1,
    'kinmuchi': '-1',
    'occupation1': '-1',
    'occupation2': '-1',
    'occupation3': '-1',
    'occupation4': '-1',
    'occupation5': '-1',
    'education_type': '-1',
    'gakureki': '-1'
}
for col_name in defect_value:
    data[col_name] = data[col_name].fillna(defect_value[col_name])

##例外処理
data['wanted_annualpay'] = data['wanted_annualpay'].astype('str')
f = lambda x :x.split('～')[0]
data['wanted_annualpay'] = data['wanted_annualpay'].apply(f)
data['wanted_annualpay'] = data['wanted_annualpay'].replace('', str(151))
data['wanted_annualpay'] = data['wanted_annualpay'].astype(int)

##外れ値補完
outelier_value_lower = {
    'age': 18,
    'age_lower': 18,
    'age_upper': 18,
    'wanted_annualpay': 200,
    'annualpay': 100
}
outelier_value_upper = {
    'age': 80,
    'age_lower': 60,
    'age_upper': 70,
    'wanted_annualpay': 1200,
    'annualpay': 1500
}
for col_name in outelier_value_lower:
    data.loc[data[col_name] <= outelier_value_lower[col_name], col_name] = outelier_value_lower[col_name]
    data.loc[data[col_name] >= outelier_value_upper[col_name], col_name] = outelier_value_upper[col_name]

print('preprocess_done')

data['age_match'] = (data['age_upper'] - data['age'] - mean(data['age_upper'] - data['age'])) *1.0 /stdev(data['age_upper'] - data['age'])
print('age_done')

data['gender_match'] = [ 1 if data.loc[n, 'gender'] == data.loc[n, 'sex'] else 0 for n in set(data.index)]
data['gender_match']
print('gender_done')

data['salary_match'] = (data['wanted_annualpay'] - data['annualpay'] - mean(data['wanted_annualpay'] - data['annualpay'])) *1.0 /stdev(data['wanted_annualpay'] - data['annualpay'])
print('salary_done')

##exp_match
for col_name in ['exp_id', 'user_exp_id']:
    data[col_name] = data[col_name].fillna('0').str.split(',').replace('', '0')
    data[col_name] = [ [int(str) if str != '' else 0 for str in element] for element in data[col_name]  ]
for col_name in ['exp_check_number', 'user_exp_check_number']:
    data[col_name] = data[col_name].fillna('0').str.split(',').replace('', '0')
    data[col_name] = [ [float(str) if str != '' else 0 for str in element] for element in data[col_name]  ]
data['exp_level_vector'] = [ [ [ row.exp_check_number[row.exp_id.index(n)]][0] if n in row.exp_id else 0 for n in range(1,1009)] for row in data.itertuples()]
data['user_exp_level_vector'] = [ [ [ row.user_exp_check_number[row.user_exp_id.index(n)]][0] if n in row.user_exp_id else 0 for n in range(1,1009)] for row in data.itertuples()]
# weight = {1: 0.05, 2: 0.1, 3: 1.0}
weight = {1: 0.5, 2: 0.7, 3: 1.0}
data['exp_level_vector'] = [pd.DataFrame(data['exp_level_vector'][n]).replace(weight).T.values.tolist()[0] for n in range(len(data))]
data['user_exp_level_vector'] = [pd.DataFrame(data['user_exp_level_vector'][n]).replace(weight).T.values.tolist()[0] for n in range(len(data))]
##類似度行列にはexp_idの欠損があるので、それを補う
index_list = pd.DataFrame({'exp_id_a' : [ n for n in range(1,1009) for m in range(1,1009)], 'exp_id_b' : [ m for n in range(1,1009) for m in range(1,1009)]})
exp_similarity_converter = pd.merge(index_list, exp_similarity_converter, on = ['exp_id_a', 'exp_id_b'], how = 'left').fillna(0)
##クロス集計して縦横がexp_idに対応するようにする
tally = pd.pivot_table(exp_similarity_converter, values='similarity', index='exp_id_a', columns='exp_id_b')
##exp_level_vectorにこの類似度行列を作用させ、ひとつのexp_idに紐つく複数の類似exp_idに成分を持たせる
data['exp_level_vector'] = [np.dot(tally, row.exp_level_vector) for row in data.itertuples()]
##exp_level_vectorの全成分が0のケースだけ例外処理する
data['exp_level_vector_len'] = [np.linalg.norm(row.exp_level_vector, ord=2) for row in data.itertuples()]
data['exp_level_vector'] = [pd.DataFrame(data['exp_level_vector'][n]).replace({0.0:0.05}).T.values.tolist()[0] if data['exp_level_vector_len'][n] == 0.0 else data['exp_level_vector'][n] for n in range(len(data))]
##exp_level_vectorとuser_exp_level_vectorのベクトル類似度を計算する
data['exp_match'] = [np.dot(row.exp_level_vector, row.user_exp_level_vector) *1.0 /max( np.linalg.norm(row.exp_level_vector, ord=2) * np.linalg.norm(row.user_exp_level_vector, ord=2), 1 ) for row in data.itertuples()]
data['exp_match'] = data['exp_match'].fillna(0)
data = data.drop(['exp_id', 'exp_check_number', 'user_exp_id', 'user_exp_check_number', 'exp_level_vector', 'user_exp_level_vector'], axis=1)
print('exp_done')

##licentiate_match
for col_name in ['licentiate_id', 'user_licentiate_id']:
    data[col_name] = data[col_name].fillna('0').str.split(',').replace('', '0')
    data[col_name] = [ [int(str) if str != '' else 0 for str in element] for element in data[col_name]  ]
data['licentiate_vector'] = [ [ 1 if n in row.licentiate_id else 0 for n in range(1, 2070) ] for row in data.itertuples()]
data['user_licentiate_vector'] = [ [ 1 if n in row.user_licentiate_id else 0 for n in range(1, 2070) ] for row in data.itertuples()]
##類似度行列にはexp_idの欠損があるので、それを補う
index_list = pd.DataFrame({'licentiate_id_a' : [ n for n in range(1,2070) for m in range(1,2070)], 'licentiate_id_b' : [ m for n in range(1,2070) for m in range(1,2070)]})
licentiate_similarity_converter = pd.merge(index_list, licentiate_similarity_converter, on = ['licentiate_id_a', 'licentiate_id_b'], how = 'left').fillna(0)
licentiate_similarity_converter.loc[(licentiate_similarity_converter.licentiate_id_b == licentiate_similarity_converter.licentiate_id_a), 'similarity'] = 1.0
##クロス集計して縦横がexp_idに対応するようにする
tally = pd.pivot_table(licentiate_similarity_converter, values='similarity', index='licentiate_id_a', columns='licentiate_id_b')
##licentiate_vectorにこの類似度行列を作用させ、ひとつの#licentiate_idに紐つく複数の類似#licentiate_idに成分を持たせる
data['licentiate_vector'] = [np.dot(row.licentiate_vector, tally) for row in data.itertuples()]
##licentiate_vectorの全成分が0のケースだけ例外処理する
data['licentiate_vector_len'] = [np.linalg.norm(row.licentiate_vector, ord=2) for row in data.itertuples()]
data['licentiate_vector'] = [pd.DataFrame(data['licentiate_vector'][n]).replace({0.0:0.05}).T.values.tolist()[0] if data['licentiate_vector_len'][n] == 0.0 else data['licentiate_vector'][n] for n in range(len(data))]
data['licentiate_match'] = [np.dot(row.licentiate_vector, row.user_licentiate_vector) *1.0 /max( np.linalg.norm(row.licentiate_vector, ord=2) * np.linalg.norm(row.user_licentiate_vector, ord=2), 1) for row in data.itertuples()]
data['licentiate_match'] = data['licentiate_match'].fillna(0)
data = data.drop(['licentiate_id', 'user_licentiate_id', 'licentiate_vector', 'user_licentiate_vector'], axis=1)
print('licentiate_done')

#データを出力する
params = [
    'member_id',
    'work_id',
    'age_match',
    'salary_match',
    'gender_match',
    'exp_match',
    'licentiate_match',
    'hire_flg'
]
data[params].to_csv("preprocess_training.csv")
