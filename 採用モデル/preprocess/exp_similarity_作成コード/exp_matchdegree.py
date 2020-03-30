import pandas as pd
import numpy as np
import itertools
import ipdb

exp_vec = pd.read_csv('/Users/200510/Desktop/TN/matchscout/prehire/改善/exp_hirerate_similarity/exp_rating_matrix.csv')
tally = pd.pivot_table(exp_vec,values='hire_rate',index='work_id',columns='exp_id')
tally = tally.fillna(0)

# df = pd.DataFrame(columns = ['exp_id_a', 'exp_id_b', 'similarity'])
# for a, b in itertools.product(tally, tally):
#     vec_a = tally[:][a]
#     vec_b = tally[:][b]
#     simil = sum(vec_a * vec_b) *1.0 / ( np.sqrt(sum(vec_a * vec_a)) * np.sqrt(sum(vec_b * vec_b)) )
#     tmp = pd.Series( [ int(a), int(b), simil ], index = df.columns )
#     df = df.append( tmp, ignore_index = True )
#     print(a, b, simil)

df = [
    pd.Series(
        [
            int(a)
            ,int(b)
            ,sum(tally[:][a] * tally[:][b]) *1.0 / ( np.sqrt(sum(tally[:][a] * tally[:][a])) * np.sqrt(sum(tally[:][b] * tally[:][b])) )
        ]
        , index =  ['exp_id_a', 'exp_id_b', 'similarity']
    )
    for a, b in itertools.product(tally, tally)
]

df.to_csv("exp_similarity.csv", index = False)

ipdb.set_trace()
