import unittest
from unittest.mock import Mock, patch

from app.retrieval import retrieve_documents


class RetrievalTests(unittest.TestCase):
    @patch("app.retrieval.config.TOP_K", 2)
    @patch("app.retrieval.config.RETRIEVAL_FETCH_K", 8)
    @patch("app.retrieval.config.MAX_RETRIEVAL_DISTANCE", 1.0)
    @patch("app.retrieval.get_vector_db")
    def test_filters_distant_and_duplicate_chunks(self, get_vector_db):
        first = Mock(page_content="Policy text.", metadata={"page": 1})
        duplicate = Mock(page_content="  POLICY   text. ", metadata={"page": 2})
        second = Mock(page_content="Another useful excerpt.", metadata={"page": 3})
        distant = Mock(page_content="Unrelated text.", metadata={"page": 4})
        database = Mock()
        database.similarity_search_with_score.return_value = [
            (first, 0.2),
            (duplicate, 0.3),
            (distant, 1.01),
            (second, 0.8),
        ]
        get_vector_db.return_value = database

        results = retrieve_documents("  What   is the policy?  ")

        self.assertEqual(results, [(first, 0.2), (second, 0.8)])
        database.similarity_search_with_score.assert_called_once_with(
            query="What is the policy?",
            k=8,
        )

    @patch("app.retrieval.get_vector_db")
    def test_blank_query_does_not_load_vector_database(self, get_vector_db):
        self.assertEqual(retrieve_documents(" \t "), [])
        get_vector_db.assert_not_called()
