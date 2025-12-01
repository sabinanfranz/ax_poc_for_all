import json
from types import SimpleNamespace
from unittest import TestCase, mock

from core.research import JobResearchJSONError, run_job_research


def _make_response(
    text: str,
    query_count: int = 0,
    include_chunks: bool = True,
):
    queries = [f"q{i}" for i in range(query_count)]
    chunks = []
    if include_chunks:
        chunks = [SimpleNamespace(web=SimpleNamespace(uri="http://example.com", title="Example"))]
    grounding_metadata = SimpleNamespace(web_search_queries=queries, grounding_chunks=chunks)
    candidate = SimpleNamespace(grounding_metadata=grounding_metadata)
    return SimpleNamespace(text=text, candidates=[candidate])


class RunJobResearchTests(TestCase):
    def setUp(self) -> None:
        self.payload = {
            "job_run_id": "jr_123",
            "company_name": "Acme Corp",
            "job_title": "Data Engineer",
            "manual_jd_text": None,
            "locale": "ko",
            "max_tokens": None,
        }

    def test_happy_path_parses_and_maps_metadata(self) -> None:
        good_json = json.dumps(
            {
                "raw_job_desc": "Data engineer role summary",
                "sources": [
                    {
                        "url": "http://example.com/jd",
                        "title": "JD",
                        "snippet": "JD snippet",
                        "source_type": "job_posting",
                        "language": "en",
                    }
                ],
            }
        )
        fake_response = _make_response(text=good_json, query_count=2)

        with mock.patch("core.research.generate_with_web_search", return_value=fake_response):
            output = run_job_research(self.payload)

        self.assertEqual(output["research_sources"][0]["rank"], 1)
        self.assertEqual(output["llm_metadata"]["grounding_query_count"], 2)
        self.assertTrue(output["raw_job_desc"])
        # Ensure JSON serializable
        json.dumps(output)

    def test_retry_on_bad_json_then_succeeds(self) -> None:
        bad_response = _make_response(text="{ not json }", query_count=0, include_chunks=False)
        good_json = json.dumps({"raw_job_desc": "OK", "sources": []})
        good_response = _make_response(text=good_json, query_count=1, include_chunks=False)

        with mock.patch(
            "core.research.generate_with_web_search",
            side_effect=[bad_response, good_response],
        ):
            output = run_job_research(self.payload)

        self.assertEqual(output["raw_job_desc"], "OK")
        self.assertEqual(output["llm_metadata"]["grounding_query_count"], 1)

    def test_raises_after_two_bad_json_responses(self) -> None:
        bad_response_1 = _make_response(text="not json 1", include_chunks=False)
        bad_response_2 = _make_response(text="not json 2", include_chunks=False)

        with mock.patch(
            "core.research.generate_with_web_search",
            side_effect=[bad_response_1, bad_response_2],
        ):
            with self.assertRaises(JobResearchJSONError):
                run_job_research(self.payload)
