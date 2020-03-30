import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegressionCV
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn import metrics
from imblearn.under_sampling import RandomUnderSampler
import matplotlib.pyplot as plt

#インプット
data = pd.read_csv("preprocess/preprocess_training.csv")
explain = [
    'age_match',
    # 'salary_match',
    'gender_match',
    'exp_match',
    'licentiate_match',
]
object = 'hire_flg'

# 統計モデルの選択
X_train, X_test = train_test_split(
    data,
    test_size = 0.10
)

##実装速度が早くなり、学習精度も下がらないのでアンダーサンプリングで対処します
sampler = RandomUnderSampler(random_state=1)
X_resampled, y_resampled = sampler.fit_resample(X_train[explain], X_train[object])

model = LogisticRegressionCV(
    penalty = 'l2',
    solver = 'saga',
    class_weight = 'balanced',
    Cs = np.logspace(-10, 0, 100),
    fit_intercept = True,
    cv = 100,##交差検証の回数
    scoring = 'roc_auc',
    n_jobs = -1,##使用コア数
)

# 推定の実行
model.fit(X_resampled, y_resampled)
print('auc_score', model.score(X_test[explain], X_test[object]))

##精度検証
Y_pred = model.predict(X_test[explain])
Y_prob = model.predict_proba(X_test[explain])[:,1]
Y_actual = X_test[object]
print('recall', metrics.recall_score(Y_actual, Y_pred))
print('accuracy', metrics.accuracy_score(Y_actual, Y_pred))
print('precision', metrics.precision_score(Y_actual, Y_pred))
print('confusion matrix', metrics.confusion_matrix(Y_actual,Y_pred))
print('C',model.C_)
print('-------coef-------')
coef = dict(zip(explain, model.coef_.tolist()[0]))
for key in coef:
    print(key, ':', coef[key])
print('------------------')

##ユーザー抽出データへスコアを書き込む
data = pd.read_csv("zip/応募モデル/entry_prediction_result.csv")
prob = model.predict_proba(data[explain])
data['Y_prob_prehire'] = prob[:,1]
data['Y_prob_entry_prehire'] = data['Y_prob'] * data['Y_prob_prehire']
data.to_csv('matchscore.csv')
