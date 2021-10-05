import inspect
import unittest
import warnings
from importlib import import_module
from os import path

import numpy as np
from sklearn.datasets import make_blobs

from skactiveml import pool
from skactiveml.classifier import PWC, CMM
from skactiveml.utils import call_func, is_unlabeled, MISSING_LABEL


class TestGeneral(unittest.TestCase):

    def setUp(self):
        self.MISSING_LABEL = MISSING_LABEL
        self.X, self.y_true = make_blobs(n_samples=10, n_features=2, centers=2,
                                         cluster_std=1, random_state=1)
        self.budget = 5

        self.query_strategies = {}
        # TODO Check is class.
        for qs_name in pool.__all__:
            if qs_name[0].isupper():
                self.query_strategies[qs_name] = getattr(pool, qs_name)
        print(self.query_strategies.keys())

    def test_al_cycle(self):
        for qs_name in self.query_strategies:
            if qs_name == "FourDS":
                clf = CMM(classes=np.unique(self.y_true),
                          missing_label=MISSING_LABEL,
                          random_state=np.random.RandomState(0))
            else:
                clf = PWC(classes=np.unique(self.y_true),
                          missing_label=MISSING_LABEL,
                          random_state=np.random.RandomState(0))

            with self.subTest(msg="Random State", qs_name=qs_name):
                y = np.full(self.y_true.shape, self.MISSING_LABEL)
                qs = call_func(
                    self.query_strategies[qs_name], only_mandatory=False,
                    classes=np.unique(self.y_true),
                    random_state=np.random.RandomState(0), clf=clf,
                )

                unlabeled = np.where(is_unlabeled(y))[0]
                id1, u1 = call_func(qs.query, X_cand=self.X[unlabeled],
                                    X=self.X, y=y, clf=clf, X_eval=self.X,
                                    return_utilities=True)
                id2, u2 = call_func(qs.query, X_cand=self.X[unlabeled],
                                    X=self.X, y=y, clf=clf, X_eval=self.X,
                                    return_utilities=True)
                np.testing.assert_array_equal(id1, id2)
                np.testing.assert_array_equal(u1, u2)

            with self.subTest(msg="Batch",
                              qs_name=qs_name):
                y = np.full(self.y_true.shape, self.MISSING_LABEL)
                qs = call_func(
                    self.query_strategies[qs_name], only_mandatory=True,
                    clf=clf, classes=np.unique(self.y_true),
                    random_state=np.random.RandomState(0))

                ids, u = call_func(qs.query, X_cand=self.X[unlabeled],
                                   X=self.X, y=y, clf=clf, X_eval=self.X,
                                   batch_size=5, return_utilities=True)
                self.assertEqual(len(ids), 5)
                self.assertEqual(len(u), 5, msg='utility score should '
                                                'have shape (5xN)')
                self.assertEqual(len(u[0]), len(unlabeled),
                                 msg='utility score must have shape (5xN)')

                self.assertWarns(Warning, call_func, f_callable=qs.query,
                                 X_cand=self.X[unlabeled], X=self.X, y=y,
                                 clf=clf, X_eval=self.X, batch_size=15)

                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    ids = call_func(qs.query, X_cand=self.X[unlabeled],
                                    X=self.X, y=y, X_eval=self.X,
                                    clf=clf, batch_size=15)
                    self.assertEqual(len(ids), 10)

            for init_budget in [5, 1, 0]:
                y = np.full(self.y_true.shape, self.MISSING_LABEL)
                y[0:init_budget] = self.y_true[0:init_budget]

                with self.subTest(msg="Basic AL Cycle",
                                  init_budget=init_budget, qs_name=qs_name):
                    qs = call_func(
                        self.query_strategies[qs_name], only_mandatory=True,
                        clf=clf, classes=np.unique(self.y_true),
                        random_state=1)

                    unlabeled = np.where(is_unlabeled(y))[0]

                    for b in range(self.budget):
                        unlabeled = np.where(is_unlabeled(y))[0]
                        clf.fit(self.X, y)
                        ids = call_func(qs.query, X_cand=self.X[unlabeled],
                                        clf=clf, X=self.X, y=y, X_eval=self.X)
                        sample_id = unlabeled[ids]
                        y[sample_id] = self.y_true[sample_id]

    def test_param(self):
        not_test = ['self', 'kwargs', 'random_state', 'X_cand', 'X', 'y',
                    'clf', 'batch_size', 'return_utilities', 'refit']
        for qs_name in self.query_strategies:
            with self.subTest(msg="Param Test", qs_name=qs_name):
                # Get initial parameters.
                qs_class = self.query_strategies[qs_name]
                init_params = inspect.signature(qs_class).parameters.keys()
                init_params = list(init_params)

                # Get query parameters.
                query_params = inspect.signature(qs_class.query).parameters
                query_params = list(query_params.keys())

                # Check initial parameters.
                values = [Dummy() for i in range(len(init_params))]
                qs_obj = qs_class(*values)
                for param, value in zip(init_params, values):
                    self.assertTrue(
                        hasattr(qs_obj, param),
                        msg=f'"{param}" not tested for __init__()')
                    self.assertEqual(getattr(qs_obj, param), value)

                # Get class to check.
                class_filename = path.basename(inspect.getfile(qs_class))[:-3]
                mod = 'skactiveml.pool.tests.test' + class_filename
                mod = import_module(mod)
                test_class_name = 'Test' + qs_class.__name__
                msg = f'{qs_name} has no test called {test_class_name}.'
                self.assertTrue(hasattr(mod, test_class_name), msg=msg)
                test_obj = getattr(mod, test_class_name)

                # Check init parameters.
                for param in np.setdiff1d(init_params, not_test):
                    test_func_name = 'test_init_param_' + param
                    self.assertTrue(
                        hasattr(test_obj, test_func_name),
                        msg="'{}()' missing for parameter '{}' of "
                            "__init__()".format(test_func_name, param))

                # Check query parameters.
                for param in np.setdiff1d(query_params, not_test):
                    test_func_name = 'test_query_param_' + param
                    msg = f"'{test_func_name}()' missing for parameter " \
                          f"'{param}' of query()"
                    self.assertTrue(hasattr(test_obj, test_func_name), msg)


class Dummy:
    def __init__(self):
        pass
