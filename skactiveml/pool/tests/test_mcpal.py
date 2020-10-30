import numpy as np
import unittest

from skactiveml.pool import McPAL
from skactiveml.classifier import PWC
from skactiveml.utils import MISSING_LABEL


class TestMCPAL(unittest.TestCase):

    def setUp(self):
        self.X = np.zeros((6, 2))
        self.weights = np.ones(len(self.X)) / len(self.X)
        self.X_cand = np.zeros((2, 2))
        self.y = [0, 1, 1, 0, 2, 1]
        self.classes = [0, 1, 2]
        self.C = np.eye(3)
        self.clf = PWC(classes=self.classes)

    def test_init(self):
        self.assertRaises(TypeError, McPAL)
        pal = McPAL(clf=3)
        self.assertRaises(TypeError, pal.query, self.X_cand, self.X, self.y,
                          self.weights)
        self.assertRaises(ValueError, McPAL, self.clf, self.classes,
                          random_state='string')
        pal = McPAL(self.clf, prior=0)
        self.assertRaises(ValueError, pal.query, self.X_cand, self.X, self.y,
                          self.weights)
        pal = McPAL(self.clf, prior='wrong_value')
        self.assertRaises(TypeError, pal.query, self.X_cand, self.X, self.y,
                          self.weights)
        pal = McPAL(self.clf, m_max=-2)
        self.assertRaises(ValueError, pal.query, self.X_cand, self.X, self.y,
                          self.weights)
        pal = McPAL(self.clf, m_max=1.5)
        self.assertRaises(ValueError, pal.query, self.X_cand, self.X, self.y,
                          self.weights)

    def test_query(self):
        mcpal = McPAL(clf=self.clf)
        self.assertRaises(ValueError, mcpal.query, X_cand=[], X=[], y=[],
                          weights=[])
        self.assertRaises(ValueError, mcpal.query, X_cand=[], X=self.X,
                          y=self.y, weights=self.weights)
        self.assertRaises(ValueError, mcpal.query, X_cand=self.X_cand,
                          X=self.X, y=[0, 1, 4, 0, 2, 1], weights=self.weights)

    def test_missing_label(self):
        X_cand = [[0], [1], [2]]
        mcpal = McPAL(clf=PWC(classes=[0, 1]))
        _, utilities = mcpal.query(X_cand, [[1]], [MISSING_LABEL],
                                   return_utilities=True, weights=[1])
        self.assertEqual(utilities.shape, (1, len(X_cand)))
        self.assertEqual(len(np.unique(utilities)), 1)

        _, utilities = mcpal.query(X_cand, X=[[0], [1], [2]],
                                   y=[0, 1, MISSING_LABEL], weights=[1, 1, 1],
                                   return_utilities=True)
        self.assertGreater(utilities[0, 2], utilities[0, 1])
        self.assertGreater(utilities[0, 2], utilities[0, 0])

    def test_scenario(self):
        X_cand = [[0], [1], [2], [5]]
        mcpal = McPAL(clf=PWC(classes=[0, 1]))

        best_indices = mcpal.query(X_cand, X=[[1]], y=[0],
                                   weights=[1, 1, 1, 1])
        np.testing.assert_array_equal(best_indices, np.array([3]))

        utilities = mcpal.query(X_cand, X=[[1]], y=[0], weights=[1, 1, 1, 1],
                                return_utilities=True)[1]
        min_utilities = np.argmin(utilities)
        np.testing.assert_array_equal(min_utilities, np.array([1]))

        best_indices = mcpal.query(X_cand=[[0], [1], [2]], X=[[0], [2]],
                                   y=[0, 1], weights=[1, 1, 1])
        np.testing.assert_array_equal(best_indices, [1])


if __name__ == '__main__':
    unittest.main()