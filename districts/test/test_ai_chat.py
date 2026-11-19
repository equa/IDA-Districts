# coding=utf-8
"""AI assistant without the API (OpenSpec change ai-chat-panel, spec ai-chat): the conversation loop with a fake backend
(text, tool calls, failing tool, refusal, max_tokens, pause_turn, Stop, cost limit), the request shape, the costs,
the export, the API errors of the SDK.

    python -m pytest test/test_ai_chat.py -v
"""
import copy
import json
from types import SimpleNamespace

import pytest

from districts.ai import conversation as conv
from districts.ai.costs import PRICES, SessionCosts, stepCost
from districts.ai.export import conversationHtml

TOOLS = [{'name': 'run_checks', 'description': 'checks', 'inputSchema': {'type': 'object', 'properties': {}}},
         {'name': 'result_series', 'description': 'series', 'inputSchema': {'type': 'object', 'properties': {}}},
         {'name': 'features', 'description': 'features', 'inputSchema': {'type': 'object', 'properties': {}}}]


def text(t):
    return SimpleNamespace(type='text', text=t)


def tool_use(tid, name, args=None):
    return SimpleNamespace(type='tool_use', id=tid, name=name, input=args or {})


def message(blocks, stop, model='claude-opus-5-5', usage=None, details=None):
    return SimpleNamespace(content=blocks, stop_reason=stop, model=model, stop_details=details,
                           usage=usage or SimpleNamespace(input_tokens=1000, output_tokens=100, cache_creation_input_tokens=0, cache_read_input_tokens=0))


class FakeBackend:
    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    def step(self, params, on_text):
        self.requests.append(copy.deepcopy({k: v for k, v in params.items() if k != 'messages'}) | {'messages': json.loads(json.dumps(
            params['messages'], default=lambda o: vars(o)))})
        msg = self.script.pop(0)
        for block in msg.content:
            if block.type == 'text':
                on_text(block.text)
        return msg


class Hooks(conv.Callbacks):
    def __init__(self, stop_after=None, continue_answer=False):
        self.texts, self.tools, self.notes, self.asked = [], [], [], 0
        self.stop_after, self.continue_answer = stop_after, continue_answer

    def text(self, delta):
        self.texts.append(delta)

    def tool(self, entry):
        self.tools.append(entry)

    def note(self, t):
        self.notes.append(t)

    def confirmContinue(self, costs):
        self.asked += 1
        return self.continue_answer

    def stopped(self):
        return self.stop_after is not None and len(self.tools) >= self.stop_after


def run_tool(name, args):
    if name == 'result_series':
        return 'no version loaded', True
    return {'tool': name, 'findings': [{'rule': 'delta_t_low', 'feature_id': 17}]}, False


def test_question_with_two_tool_calls():
    backend = FakeBackend([message([text('Checking.'), tool_use('t1', 'run_checks', {'scope': 'results'})], 'tool_use'),
                           message([tool_use('t2', 'result_series', {'table': 'x'}), tool_use('t3', 'features', {'layer': 'customers'})], 'tool_use'),
                           message([text('Customer 17 has a low ΔT.')], 'end_turn')])
    c = conv.Conversation(backend, 'claude-opus-5-5')
    hooks = Hooks()
    assert c.ask('Why?', 'Loaded: project p, version v.', TOOLS, run_tool, hooks) == 'end_turn'
    assert [e['name'] for e in hooks.tools] == ['run_checks', 'result_series', 'features']
    assert hooks.tools[1]['is_error'] and hooks.tools[1]['result'] == 'no version loaded'
    # the third request carries both results of the second turn in one user message
    last = backend.requests[2]['messages'][-1]
    assert last['role'] == 'user' and [r['tool_use_id'] for r in last['content']] == ['t2', 't3']
    assert last['content'][0]['is_error'] is True and last['content'][1]['is_error'] is False
    assert backend.requests[0]['messages'][0]['content'][0]['text'].startswith('Loaded: project p, version v.')
    assert ''.join(hooks.texts) == 'Checking.Customer 17 has a low ΔT.'
    assert [e['role'] for e in c.transcript] == ['user', 'assistant', 'tool', 'tool', 'tool', 'assistant']


def test_request_shape():
    backend = FakeBackend([message([text('hi')], 'end_turn')])
    conv.Conversation(backend, 'claude-opus-5-5', 'high').ask('q', 'ctx', TOOLS, run_tool, Hooks())
    r = backend.requests[0]
    assert [t['name'] for t in r['tools']] == ['features', 'result_series', 'run_checks']
    assert r['fallbacks'] == 'default' and r['betas'] == [conv.FALLBACK_BETA]
    assert r['output_config'] == {'effort': 'high'} and r['cache_control'] == {'type': 'ephemeral'}
    assert r['system'] == conv.SYSTEM_PROMPT and 'ctx' not in r['system']
    backend = FakeBackend([message([text('hi')], 'end_turn', model='claude-haiku-5-5')])
    conv.Conversation(backend, 'claude-haiku-5-5').ask('q', 'ctx', TOOLS, run_tool, Hooks())
    assert 'fallbacks' not in backend.requests[0] and backend.requests[0]['betas'] == []


def test_tool_not_allowed_is_not_run():
    ran = []
    backend = FakeBackend([message([tool_use('t1', 'render_map')], 'tool_use'), message([text('ok')], 'end_turn')])
    conv.Conversation(backend, 'claude-opus-5-5').ask('q', 'ctx', TOOLS, lambda n, a: ran.append(n), Hooks())
    assert not ran
    result = backend.requests[1]['messages'][-1]['content'][0]
    assert result['is_error'] and 'not allowed' in result['content'][0]['text']


def test_refusal_ends_and_keeps_the_history_valid():
    details = SimpleNamespace(category='cyber')
    backend = FakeBackend([message([tool_use('t1', 'run_checks')], 'refusal', details=details)])
    c = conv.Conversation(backend, 'claude-opus-5-5')
    hooks = Hooks()
    c.ask('q', 'ctx', TOOLS, run_tool, hooks)
    assert 'cyber' in hooks.notes[0] and len(backend.requests) == 1
    assert c.history[-1]['content'][0]['tool_use_id'] == 't1' and c.history[-1]['content'][0]['is_error']


def test_max_tokens_and_pause_turn():
    backend = FakeBackend([message([text('a')], 'pause_turn'), message([text('b')], 'max_tokens')])
    hooks = Hooks()
    conv.Conversation(backend, 'claude-opus-5-5').ask('q', 'ctx', TOOLS, run_tool, hooks)
    assert len(backend.requests) == 2 and 'maximum length' in hooks.notes[0]


def test_stop_between_steps():
    backend = FakeBackend([message([tool_use('t1', 'run_checks')], 'tool_use'), message([text('never')], 'end_turn')])
    hooks = Hooks(stop_after=1)
    conv.Conversation(backend, 'claude-opus-5-5').ask('q', 'ctx', TOOLS, run_tool, hooks)
    assert len(backend.requests) == 1 and hooks.notes == ['stopped by the user']


def test_cost_limit_asks_before_the_next_request():
    big = SimpleNamespace(input_tokens=500000, output_tokens=0, cache_creation_input_tokens=0, cache_read_input_tokens=0)  # 2.00 USD
    backend = FakeBackend([message([tool_use('t1', 'run_checks')], 'tool_use', usage=big), message([text('more')], 'end_turn')])
    hooks = Hooks(continue_answer=False)
    c = conv.Conversation(backend, 'claude-opus-5-5', costs=SessionCosts(2.0))
    c.ask('q', 'ctx', TOOLS, run_tool, hooks)
    assert hooks.asked == 1 and len(backend.requests) == 1 and 'cost limit' in hooks.notes[0]
    backend.script = [message([text('more')], 'end_turn')]
    hooks = Hooks(continue_answer=True)
    c.ask('q2', 'ctx', TOOLS, run_tool, hooks)
    assert hooks.asked == 1 and c.costs.limit == pytest.approx(4.0) and len(backend.requests) == 2


def test_cost_of_a_step():
    usage = {'input_tokens': 10000, 'cache_read_input_tokens': 50000, 'output_tokens': 1000, 'cache_creation_input_tokens': 0}
    usd, known = stepCost('claude-opus-5-5', usage)
    p_in, _, p_read, p_out = PRICES['claude-opus-5-5']
    assert known and usd == pytest.approx((10000 * p_in + 50000 * p_read + 1000 * p_out) / 1e6)
    # a fallback served by an unknown model is priced like the session model and reported
    costs = SessionCosts()
    costs.add('claude-unknown', usage, 'claude-sonnet-5-5')
    assert costs.unknown_models == {'claude-unknown'} and costs.total == pytest.approx(stepCost('claude-sonnet-5-5', usage)[0])


def test_map_image_as_image_block():
    content = conv.resultContent({'image_png_base64': 'iVBOR', 'width': 10, 'height': 5})
    assert content[0] == {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': 'iVBOR'}}
    long = conv.resultContent({'rows': 'x' * (conv.MAX_RESULT_CHARS + 10)})
    assert 'result cut after' in long[0]['text']


def test_export_contains_the_conversation_and_no_key(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-secret')
    transcript = [{'role': 'user', 'text': 'Why?', 'context': 'ctx'}, {'role': 'tool', 'name': 'run_checks', 'input': {'scope': 'results'},
                  'result': {'findings': []}, 'is_error': False}, {'role': 'assistant', 'text': 'Because <b>.'}]
    page = conversationHtml(transcript, 'claude-opus-5-5', SessionCosts(), 'p', 'v')
    assert 'Why?' in page and 'run_checks' in page and '<details' in page and '&lt;b&gt;' in page
    assert 'sk-ant' not in page


def test_api_errors_name_the_key_source():
    anthropic = pytest.importorskip('anthropic')
    import httpx2 as httpx
    response = httpx.Response(401, request=httpx.Request('POST', 'https://api.anthropic.com/v1/messages'))
    error = anthropic.AuthenticationError('invalid x-api-key', response=response, body=None)
    assert 'QGIS settings' in conv.errorText(error, 'settings')
    assert conv.errorText(ValueError('x'), None) == conv.NO_KEY_TEXT


def sse(events):
    return ''.join('event: {}\ndata: {}\n\n'.format(e['type'], json.dumps(e)) for e in events).encode('utf-8')


def streamed_answer(text_value, stop='end_turn', tool=None):
    events = [{'type': 'message_start', 'message': {'id': 'msg_1', 'type': 'message', 'role': 'assistant', 'model': 'claude-opus-5-5',
               'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 10, 'output_tokens': 1}}},
              {'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}},
              {'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': text_value}},
              {'type': 'content_block_stop', 'index': 0}]
    if tool:
        events += [{'type': 'content_block_start', 'index': 1, 'content_block': {'type': 'tool_use', 'id': 'toolu_1', 'name': tool, 'input': {}}},
                   {'type': 'content_block_delta', 'index': 1, 'delta': {'type': 'input_json_delta', 'partial_json': '{"scope": "qgis"}'}},
                   {'type': 'content_block_stop', 'index': 1}]
    events += [{'type': 'message_delta', 'delta': {'stop_reason': stop, 'stop_sequence': None}, 'usage': {'output_tokens': 5}},
               {'type': 'message_stop'}]
    return sse(events)


def test_the_real_sdk_accepts_the_requests():
    """the anthropic client against a local transport: the request body, the beta header, and the SDK's own blocks
    sent back in the history of the next request"""
    anthropic = pytest.importorskip('anthropic')
    import httpx2
    answers = [streamed_answer('Checking.', 'tool_use', 'run_checks'), streamed_answer('Done.')]
    sent = []

    def handler(request):
        sent.append((dict(request.headers), json.loads(request.content)))
        return httpx2.Response(200, headers={'content-type': 'text/event-stream'}, content=answers.pop(0))

    client = anthropic.Anthropic(api_key='test-key', http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))
    c = conv.Conversation(conv.AnthropicBackend(client), 'claude-opus-5-5')
    hooks = Hooks()
    assert c.ask('q', 'ctx', TOOLS, lambda n, a: ({'ok': a}, False), hooks) == 'end_turn'
    headers, body = sent[0]
    assert 'server-side-fallback-2026-07-01' in headers.get('anthropic-beta', '')
    assert body['fallbacks'] == 'default' and body['stream'] is True and body['output_config'] == {'effort': 'medium'}
    assert hooks.tools[0]['input'] == {'scope': 'qgis'} and ''.join(hooks.texts) == 'Checking.Done.'
    _, second = sent[1]
    assert [m['role'] for m in second['messages']] == ['user', 'assistant', 'user']
    assert second['messages'][1]['content'][1] == {'type': 'tool_use', 'id': 'toolu_1', 'name': 'run_checks', 'input': {'scope': 'qgis'}}
    assert second['messages'][2]['content'][0]['tool_use_id'] == 'toolu_1'
