import unittest

import numpy as np
from sklearn.metrics import DistanceMetric
from sklearn.datasets import make_classification

from skactiveml.classifier import ParzenWindowClassifier
from skactiveml.stream import DBStream, CogDQSRan, CogDQSRanVarUn, CogDQSVarUn, CogDQSFixUn


class TemplateTestCogDQS:
    def setUp(self):
        # initialise valid data to test uncertainty parameters
        rand = np.random.RandomState(0)
        stream_length = 100
        train_init_size = 10
        X, y = make_classification(
            n_samples=stream_length + train_init_size,
            random_state=rand.randint(2 ** 31 - 1),
            shuffle=True,
        )

        self.X = X[:train_init_size, :]
        self.candidates = X[train_init_size:, :]
        self.y = y[:train_init_size]
        self.clf = ParzenWindowClassifier()
        self.kwargs = dict(
            candidates=self.candidates, clf=self.clf, X=self.X, y=self.y
        )
        self.dist_func = DistanceMetric.get_metric("manhattan").pairwise

    def test_init_param_budget(self):
        # budget must be defined as a float greater than 0
        query_strategy = self.get_query_strategy()(budget=[])
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(budget="string")
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(budget=-1)
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))

    def test_init_param_budget_manager(self):
        # budgetmanager must be defined as an object of an budget manager
        # class
        query_strategy = self.get_query_strategy()(budget_manager=[])
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))

    def test_init_param_random_state(self):
        query_strategy = self.get_query_strategy()(
            random_state="string",
        )
        self.assertRaises(ValueError, query_strategy.query, **(self.kwargs))

    def test_init_param_density_threshold(self):
        query_strategy = self.get_query_strategy()(
            density_threshold="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            density_threshold=-1,
        )
        self.assertRaises(ValueError, query_strategy.query, **(self.kwargs))

    def test_init_param_cognition_window_size(self):
        query_strategy = self.get_query_strategy()(
            cognition_window_size="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            cognition_window_size=-1,
        )
        self.assertRaises(ValueError, query_strategy.query, **(self.kwargs))

    def test_init_param_dist_func(self):
        query_strategy = self.get_query_strategy()(
            dist_func="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            dist_func=0,
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        self.assertRaises(TypeError, query_strategy.update, candidates=self.X, queried_indices=np.array([1,2]))

    def test_init_param_force_full_budget(self):
        query_strategy = self.get_query_strategy()(
            force_full_budget="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            force_full_budget=0,
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))


    def test_query_param_candidates(self):
        # candidates must be defined as a two dimensinal array
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=1,
            clf=self.clf,
            X=self.X,
            y=self.y,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=None,
            clf=self.clf,
            X=self.X,
            y=self.y,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=np.ones(5),
            clf=self.clf,
            X=self.X,
            y=self.y,
        )

    def test_query_param_clf(self):
        # clf must be defined as a classifier
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf="string",
            X=self.X,
            y=self.y,
        )
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=1,
            X=self.X,
            y=self.y,
        )

    def test_query_param_X(self):
        # X must be defined as a two dimensinal array and must be equal in
        # length to y
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=1,
            y=self.y,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=None,
            y=self.y,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=np.ones(5),
            y=self.y,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X[1:],
            y=self.y,
            fit_clf=True,
        )

    def test_query_param_y(self):
        # y must be defined as a one Dimensional array and must be equal in
        # length to X
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=1,
            fit_clf=True,
        )
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=None,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            fit_clf=True,
        )

    def test_query_param_sample_weight(self):
        # sample weight needs to be a list that can be convertet to float
        # equal in size of y
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            sample_weight="string",
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            sample_weight=["string", "numbers", "test"],
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            sample_weight=[1],
            fit_clf=True,
        )

    def test_query_param_fit_clf(self):
        # fit_clf needs to be a boolean
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            fit_clf="string",
        )
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            fit_clf=1,
        )

    def test_query_param_return_utilities(self):
        # return_utilities needs to be a boolean
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            return_utilities="string",
        )
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            return_utilities=1,
        )

    def test_query_with_force(self):
        query_strategy = self.get_query_strategy()(force_full_budget=True)
        query_strategy.query(
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            fit_clf=True
        )


class TestCogDQSRan(TemplateTestCogDQS, unittest.TestCase):
    def get_query_strategy(self):
        return CogDQSRan


class TestCogDQSRanVarUn(TemplateTestCogDQS, unittest.TestCase):
    def get_query_strategy(self):
        return CogDQSRanVarUn


class TestCogDQSVarUn(TemplateTestCogDQS, unittest.TestCase):
    def get_query_strategy(self):
        return CogDQSVarUn

    
class TestCogDQSFixUn(TemplateTestCogDQS, unittest.TestCase):
    def get_query_strategy(self):
        return CogDQSFixUn


class TestDBStream(unittest.TestCase):
    def setUp(self):
        # initialise valid data to test uncertainty parameters
        rand = np.random.RandomState(0)
        stream_length = 100
        train_init_size = 10
        X, y = make_classification(
            n_samples=stream_length + train_init_size,
            random_state=rand.randint(2 ** 31 - 1),
            shuffle=True,
        )

        self.X = X[:train_init_size, :]
        self.candidates = X[train_init_size:, :]
        self.y = y[:train_init_size]
        self.clf = ParzenWindowClassifier()
        self.kwargs = dict(
            candidates=self.candidates, clf=self.clf, X=self.X, y=self.y
        )

    def get_query_strategy(self):
        return DBStream

    def test_init_param_budget(self):
        # budget must be defined as a float greater than 0
        query_strategy = self.get_query_strategy()(budget=[])
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(budget="string")
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(budget=-1)
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))

    def test_init_param_budget_manager(self):
        # budgetmanager must be defined as an object of an budget manager
        # class
        query_strategy = self.get_query_strategy()(budget_manager=[])
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))

    def test_init_param_random_state(self):
        query_strategy = self.get_query_strategy()(
            random_state="string",
        )
        self.assertRaises(ValueError, query_strategy.query, **(self.kwargs))

    def test_init_param_window_size(self):
        query_strategy = self.get_query_strategy()(
            window_size="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            window_size=-1,
        )
        self.assertRaises(ValueError, query_strategy.query, **(self.kwargs))

    def test_init_param_dist_func(self):
        query_strategy = self.get_query_strategy()(
            dist_func="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            dist_func=0,
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        self.assertRaises(TypeError, query_strategy.update, candidates=self.X, queried_indices=np.array([1,2]))

    def test_init_param_force_full_budget(self):
        query_strategy = self.get_query_strategy()(
            force_full_budget="string",
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))
        query_strategy = self.get_query_strategy()(
            force_full_budget=0,
        )
        self.assertRaises(TypeError, query_strategy.query, **(self.kwargs))

    def test_query_param_candidates(self):
        # candidates must be defined as a two dimensinal array
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=1,
            clf=self.clf,
            X=self.X,
            y=self.y,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=None,
            clf=self.clf,
            X=self.X,
            y=self.y,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=np.ones(5),
            clf=self.clf,
            X=self.X,
            y=self.y,
        )

    def test_query_param_clf(self):
        # clf must be defined as a classifier
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf="string",
            X=self.X,
            y=self.y,
        )
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=1,
            X=self.X,
            y=self.y,
        )

    def test_query_param_X(self):
        # X must be defined as a two dimensinal array and must be equal in
        # length to y
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=1,
            y=self.y,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=None,
            y=self.y,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=np.ones(5),
            y=self.y,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X[1:],
            y=self.y,
            fit_clf=True,
        )

    def test_query_param_y(self):
        # y must be defined as a one Dimensional array and must be equal in
        # length to X
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=1,
            fit_clf=True,
        )
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=None,
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            fit_clf=True,
        )

    def test_query_param_sample_weight(self):
        # sample weight needs to be a list that can be convertet to float
        # equal in size of y
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            sample_weight="string",
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            sample_weight=["string", "numbers", "test"],
            fit_clf=True,
        )
        self.assertRaises(
            ValueError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            sample_weight=[1],
            fit_clf=True,
        )

    def test_query_param_fit_clf(self):
        # fit_clf needs to be a boolean
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            fit_clf="string",
        )
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            fit_clf=1,
        )

    def test_query_param_return_utilities(self):
        # return_utilities needs to be a boolean
        query_strategy = self.get_query_strategy()()
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            return_utilities="string",
        )
        self.assertRaises(
            TypeError,
            query_strategy.query,
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y[1:],
            return_utilities=1,
        )
    
    def test_query_with_force(self):
        query_strategy = self.get_query_strategy()(force_full_budget=True)
        query_strategy.query(
            candidates=self.candidates,
            clf=self.clf,
            X=self.X,
            y=self.y,
            fit_clf=True
        )