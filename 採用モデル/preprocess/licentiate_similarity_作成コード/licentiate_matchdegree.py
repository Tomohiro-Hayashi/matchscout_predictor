import pandas as pd
import numpy as np
import itertools
import ipdb

licentiate_vec = pd.read_csv('/Users/200510/Desktop/TN/matchscout/prehire/改善/licentiate_hirerate_similarity/licentiate_rating_matrix.csv')
tally = pd.pivot_table(licentiate_vec,values='hire_rate',index='work_id',columns='licentiate_id', aggfunc = 'count')
tally = tally.fillna(0)

ipdb.set_trace()

df = pd.DataFrame(
    [
        pd.Series(
            [a, b, np.dot(tally[:][a].tolist(), tally[:][b].tolist()) *1.0 / max( np.linalg.norm(tally[:][a].tolist(), ord=2) * np.linalg.norm(tally[:][b].tolist(), ord=2), 1 )]
            , index =  ['licentiate_id_a', 'licentiate_id_b', 'similarity']
        )
        for a, b in itertools.product(tally, tally)
    ]
)

ipdb.set_trace()

df.to_csv("licentiate_similarity.csv", index = False)
