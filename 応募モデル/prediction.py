import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegressionCV
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn import metrics
from imblearn.under_sampling import RandomUnderSampler
import matplotlib.pyplot as plt

#インプット
raw_data = pd.read_csv('preprocess/preprocess.csv')
explain = [
    'age_match',
    'annualpay_match',
    'gender_match',
    'pref_match',
    'occupation_match',
    'exp_match',
    'licentiate_match',
]
object = 'entry_flg'

X_train, X_test = train_test_split(
    raw_data,
    test_size = 0.20
)

sampler = RandomUnderSampler()
X_resampled, y_resampled = sampler.fit_resample(X_train[explain], X_train[object])

#統計モデルの選択
model = LogisticRegressionCV(
    penalty = 'l2',
    solver = 'lbfgs',
    Cs = np.logspace(-10, 10, 100),
    fit_intercept = True,
    cv = 100,##交差検証の回数
    # verbose = 3,
    scoring = 'roc_auc',
    n_jobs = -1##使用コア数
)

#推定の実行(グリッドサーチ)
model.fit(X_resampled, y_resampled)
print('score', model.score(X_test[explain], X_test[object]))
Y_pred = model.predict(X_test[explain])
Y_prob = model.predict_proba(X_test[explain])[:,1]
Y_actual = X_test[object]
print('recall', metrics.recall_score(Y_actual, Y_pred))
print('accuracy', metrics.accuracy_score(Y_actual, Y_pred))
print('precision', metrics.precision_score(Y_actual, Y_pred))
print('confusion matrix', metrics.confusion_matrix(Y_actual,Y_pred))
print('logloss', metrics.log_loss(Y_actual,Y_pred))
print('C',model.C_)
print('-------coef-------')
coef = dict(zip(explain, model.coef_.tolist()[0]))
for key in coef:
    print(key, ':', coef[key])
print('------------------')

fpr, tpr, thresholds = metrics.roc_curve(X_test[object], Y_prob)
auc = metrics.auc(fpr, tpr)

# plot ROC curves
plt.plot(fpr, tpr, label='Logistic Regression (AUC = %.2f)'%auc)
plt.legend()
plt.xlim([0, 1])
plt.ylim([0, 1])
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.grid(True)
plt.show()

#モデルを実行してユーザー抽出データの回帰結果を記録
data = pd.read_csv('preprocess/preprocess_target.csv')
prob = model.predict_proba(data[explain])
data['Y_prob'] = pd.DataFrame(prob[:,1], columns = ['Y_prob'])##series型からデータフレームに変換Y = model.predict_proba(X_train)
data.to_csv("entry_prediction_result.csv", index = False)
