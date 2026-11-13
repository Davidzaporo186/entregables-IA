import json
from unittest.mock import patch
import pytest
from src.agent import ask_llm
from src.rag import search_docs
from scripts.evaluate_agent import CASES


def test_rag_retrieval_sources():
    docs=search_docs('excedencias PM2.5 y muestras diarias')
    assert docs and all(d['url'].startswith('https://') for d in docs)
    assert all(d['backend']=='tfidf' for d in docs)


def test_rag_invalid_query():
    assert search_docs('   ') == []


def test_rag_invalid_backend():
    with pytest.raises(ValueError):
        search_docs('PM2.5',backend='foo')


def test_twelve_cases_defined():
    assert len(CASES)==12


def test_missing_key():
    with pytest.raises(ValueError):
        ask_llm('PM2.5', '')


class Response:
    def __init__(self, message):
        self.message=message
    def raise_for_status(self): pass
    def json(self): return {'choices':[{'message':self.message}]}


def test_agent_loop_calls_tool_and_cites():
    tool={'role':'assistant','content':None,'tool_calls':[{'id':'call_123','type':'function','function':{'name':'get_pm25','arguments':json.dumps({'estacion':'CEN-TRAF'})}}]}
    final={'role':'assistant','content':'CEN-TRAF 25.6 µg/m³: https://siata.gov.co/Informes_Aire/121_InformeProcuraduria_Enero2025/F-GAA-RA-82_InformeProcuraduria_Enero2025_Anexos.pdf'}
    with patch('src.agent.requests.post', side_effect=[Response(tool),Response(final)]) as mock:
        result=ask_llm('Promedio CEN-TRAF', 'clave_falsa')
    assert len(result['calls'])==1
    assert result['calls'][0]['result']['promedio_mensual_pm25']==25.6
    assert 'https://' in result['answer']
    assert len(mock.call_args_list)==2
    sent=mock.call_args_list[1].kwargs['json']['messages']
    assert any(m['role']=='tool' for m in sent)


def test_agent_handles_unknown_tool():
    tool={'role':'assistant','content':None,'tool_calls':[{'id':'call_x','type':'function','function':{'name':'unknown','arguments':'{}'}}]}
    with patch('src.agent.requests.post', side_effect=[Response(tool),Response({'role':'assistant','content':'No disponible'})]):
        result=ask_llm('ejemplo','key')
    assert 'error' in result['calls'][0]['result']


def test_max_rounds():
    tool={'role':'assistant','content':None,'tool_calls':[{'id':'call_1','type':'function','function':{'name':'get_pm25','arguments':'{"estacion":"CEN-TRAF"}'}}]}
    with patch('src.agent.requests.post',return_value=Response(tool)):
        result=ask_llm('dato','key',max_rounds=1)
    assert 'trazabilidad' in result['answer'].lower()
