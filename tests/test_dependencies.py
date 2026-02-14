import unittest

import fastapi
import openai
import pydantic
import sklearn
import uvicorn
from fastapi import FastAPI
from sklearn.linear_model import LogisticRegression


class DependencySmokeTests(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(hasattr(fastapi, "__version__"))
        self.assertTrue(hasattr(uvicorn, "__version__"))
        self.assertTrue(hasattr(pydantic, "__version__"))
        self.assertTrue(hasattr(sklearn, "__version__"))
        self.assertTrue(hasattr(openai, "__version__"))

    def test_expected_versions(self):
        self.assertEqual(fastapi.__version__, "0.115.0")
        self.assertEqual(uvicorn.__version__, "0.30.6")
        self.assertEqual(pydantic.__version__, "2.8.2")
        self.assertEqual(sklearn.__version__, "1.5.1")
        self.assertEqual(openai.__version__, "1.40.6")

    def test_fastapi_app_creation(self):
        app = FastAPI()
        self.assertIsInstance(app, FastAPI)

    def test_sklearn_model_train_predict(self):
        model = LogisticRegression(max_iter=200)
        x = [[0, 0], [1, 1], [1, 0], [0, 1]]
        y = [0, 1, 1, 0]
        model.fit(x, y)
        prediction = model.predict([[1, 1]])
        self.assertEqual(len(prediction), 1)
        self.assertIn(prediction[0], [0, 1])


if __name__ == "__main__":
    unittest.main()
