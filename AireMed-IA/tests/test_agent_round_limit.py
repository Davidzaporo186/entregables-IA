import json
from unittest.mock import patch
from src.agent import ask_llm

class MockResponse:
    def __init__(self, message):
        self.message = message
    def raise_for_status(self):
        pass
    def json(self):
        return {"choices": [{"message": self.message}]}

def test_round_limit_generates_final_response():
    posts = []
    def fake_post(url, **kwargs):
        body = kwargs["json"]
        posts.append(body)
        if body.get("tool_choice") == "none":
            return MockResponse({"role":"assistant", "content":"Datos consultados y fuente citada."})
        return MockResponse({"role":"assistant", "content":None, "tool_calls":[{
            "id":f"call_{len(posts)}", "type":"function", "function":{
                "name":"search_environmental_docs", "arguments":json.dumps({"pregunta":"PM2.5"})
            }
        }]})
    with patch("src.agent.requests.post", side_effect=fake_post), patch("src.agent.FUNCTIONS", {"search_environmental_docs":lambda pregunta:{"fuente":"https://example.org"}}) as funcs:
        result = ask_llm("Qué es PM2.5", "test", max_rounds=2)
    assert result["answer"] == "Datos consultados y fuente citada."
    assert len(result["calls"]) == 2
    assert len(posts) == 3
    assert posts[-1]["tool_choice"] == "none"
