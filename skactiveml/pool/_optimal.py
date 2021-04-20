import warnings

import itertools
from copy import deepcopy

import numpy as np
from sklearn import clone

from skactiveml.base import SingleAnnotPoolBasedQueryStrategy

from sklearn.metrics import accuracy_score, pairwise_kernels

from skactiveml.classifier import PWC
from skactiveml.utils import check_random_state, ExtLabelEncoder, rand_argmax


class Optimal(SingleAnnotPoolBasedQueryStrategy):

    def __init__(self, clf, score=accuracy_score, maximize_score=True,
                 nonmyopic_look_ahead=2,
                 similarity_metric='rbf', similarity_metric_dict=None,
                 random_state=None):
        """ An optimal Al strategy
        """
        super().__init__(random_state=random_state)

        self.clf = clf
        self.score = score
        self.maximize_score = maximize_score
        self.nonmyopic_look_ahead = nonmyopic_look_ahead
        self.similarity_metric = similarity_metric
        self.similarity_metric_dict = similarity_metric_dict
        self.random_state = random_state

    def query(self, X_cand, y_cand, X, y, X_eval, y_eval, batch_size=1,
              sample_weight_cand=None, sample_weight=None,
              sample_weight_eval=None, return_utilities=False, **kwargs):
        """

        Attributes
        ----------
        """

        X_cand, return_utilities, batch_size, random_state = \
            self._validate_data(X_cand, return_utilities, batch_size,
                                self.random_state, reset=True)

        clf = clone(self.clf, safe=False)

        if sample_weight is None:
            sample_weight = np.ones(len(X))
        if sample_weight_cand is None:
            sample_weight_cand = np.ones(len(X_cand))
        if sample_weight_eval is None:
            sample_weight_eval = np.ones(len(X_eval))

        if self.similarity_metric_dict is None:
            similarity_metric_dict = {}

        sim_cand = pairwise_kernels(X_cand, X_cand,
                                    metric=self.similarity_metric,
                                    **similarity_metric_dict)

        utilities = np.full([batch_size, len(X_cand)], np.nan, dtype=float)
        best_idx = np.full([batch_size], np.nan, dtype=int)
        for i_batch in range(batch_size):
            unlbld_cand_idx = np.setdiff1d(np.arange(len(X_cand)), best_idx)

            X_ = np.concatenate([X_cand, X_cand[best_idx[:i_batch]], X], axis=0)
            y_ = np.concatenate([y_cand, y_cand[best_idx[:i_batch]], y], axis=0)
            sample_weight_ = np.concatenate([sample_weight_cand,
                                             sample_weight_cand[best_idx[:i_batch]],
                                             sample_weight])

            if isinstance(clf, PWC):
                K = pairwise_kernels(X_eval, X_,
                                          metric=clf.metric,
                                          **clf.metric_dict)
                clf.metric = 'precomputed'
                clf.metric_dict = {}

            lbld_idx_ = list(range(len(X_cand), len(X_)))
            append_lbld = lambda x: list(x) + lbld_idx_

            idx_new = append_lbld([])
            X_new = X_[idx_new]
            y_new = y_[idx_new]
            sample_weight_new = sample_weight_[idx_new]
            clf_new = clf.fit(X_new, y_new, sample_weight_new)
            if isinstance(clf, PWC):
                pred_eval = clf_new.predict(K[:, idx_new])
            else:
                pred_eval = clf_new.predict(X_eval)


            old_perf = self.score(y_eval, pred_eval)  # TODO, sample_weight_eval)

            batch_utilities = np.full([len(X_cand), self.nonmyopic_look_ahead],
                                      np.nan)
            for m in range(1, self.nonmyopic_look_ahead+1):
                cand_idx_set = list(itertools.combinations(unlbld_cand_idx, m))

                for i_cand_idx, cand_idx in enumerate(cand_idx_set):
                    idx_new = append_lbld(cand_idx)
                    X_new = X_[idx_new]
                    y_new = y_[idx_new]
                    sample_weight_new = sample_weight_[idx_new]

                    clf_new = clf.fit(X_new, y_new, sample_weight_new)

                    if isinstance(clf, PWC):
                        pred_eval_new = clf_new.predict(K[:, idx_new])
                    else:
                        pred_eval_new = clf_new.predict(X_eval)

                    dperf = (self.score(y_eval, pred_eval_new) - old_perf) / m
                    if not self.maximize_score:
                        dperf *= -1
                    # TODO, sample_weight_eval)
                    batch_utilities[cand_idx, m-1] = \
                        np.nanmax([batch_utilities[cand_idx, m-1],
                                   np.full(m, dperf)],
                                  axis=0)

            max_batch_utilities = np.nanmax(batch_utilities, axis=1)
            best_idxs = np.where(max_batch_utilities == np.max(max_batch_utilities))[0]

            best_idx[i_batch] = best_idxs[rand_argmax(batch_utilities[best_idxs, 0],
                                             axis=0, random_state=random_state)]
            utilities[i_batch, :] = max_batch_utilities

        if return_utilities:
            return best_idx, utilities
        else:
            return best_idx