# coding=utf-8
"""Conversation loop of the AI assistant (OpenSpec change ai-chat-panel, D5): a manual tool loop, not the SDK tool
runner, because the tools run in the QGIS main thread (callback run_tool) and the loop pauses between requests for the
cost limit and Stop. No Qt here: the tab runs ask() in a worker thread, the tests with a fake backend."""
import json

from .costs import SessionCosts

MAX_TOKENS = 64000
MAX_RESULT_CHARS = 150000
FALLBACK_BETA = 'server-side-fallback-2026-07-01'
# server-side refusal fallback: not for Haiku 5.5, which has none
FALLBACK_MODELS = ('claude-opus-5-5', 'claude-sonnet-5-5')
EFFORTS = ('low', 'medium', 'high')
DEFAULT_EFFORT = 'medium'
NO_KEY_TEXT = ('No API key found: enter a key from an Anthropic Console account (platform.claude.com) in the Districts Modeler settings, group AI assistant. '
               'A Claude subscription (Pro, Max, Team) does not include the API: with a subscription, use the MCP connection instead '
               '(Plugins → Districts Modeler → MCP configuration ...).')

# fixed (no date, no project name): the prompt cache covers tools + system across questions and conversations
SYSTEM_PROMPT = """You are the AI assistant of the Districts Modeler, a QGIS plugin for district heating and cooling \
networks (projects and versions in PostgreSQL/PostGIS, pipe laying, topology, pipe sizing, IDA Districts simulations, \
results, economics, cost optimization). Each user message starts with the loaded project and version.

Your tools only read: the state of the project, layers and features, a map image, the model checks (run_checks), the \
result tables and logs, the template components, the key figures (version_kpis, compare_versions), the workflow state \
and the IDA Districts wiki. You cannot change data or start a job; when something has to be done, say which step of \
the Districts Modeler does it and name its wiki page (search_help, read_help_page) instead of describing menu paths \
you have not read.

Base statements about the project on tool results: run the checks or read the figures before you judge, and name the \
finding, feature id, value and threshold you rely on. Say when a result is missing, provisional (a job is running) or \
covers only representative periods. Keep answers short and concrete; answer in the language of the user's question."""


class Callbacks:
    """hooks of one question; the tab connects them to Qt signals"""

    def text(self, delta):
        pass

    def tool(self, entry):
        pass

    def note(self, text):
        pass

    def cost(self, costs):
        pass

    def confirmContinue(self, costs):
        return False

    def stopped(self):
        return False


def toolDefinitions(tools):
    """API tool definitions of the registry entries, sorted by name (a stable prefix for the prompt cache)"""
    return [{'name': t['name'], 'description': t['description'], 'input_schema': t['inputSchema']}
            for t in sorted(tools, key=lambda t: t['name'])]


def resultContent(result):
    """tool_result content of a tool's return value: a map image as image block, everything else as JSON text"""
    if isinstance(result, dict) and 'image_png_base64' in result:
        meta = {k: v for k, v in result.items() if k != 'image_png_base64'}
        return [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': result['image_png_base64']}},
                {'type': 'text', 'text': json.dumps(meta)}]
    from ..mcp.tools import jsonValue
    text = json.dumps(result, default=jsonValue, ensure_ascii=False)
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + '\n[result cut after {} characters; ask for fewer rows or a summary]'.format(MAX_RESULT_CHARS)
    return [{'type': 'text', 'text': text}]


def blockType(block):
    return block.get('type') if isinstance(block, dict) else getattr(block, 'type', None)


def blockText(blocks):
    return ''.join(getattr(b, 'text', '') or '' for b in blocks if blockType(b) == 'text')


class Conversation:
    def __init__(self, backend, model, effort=DEFAULT_EFFORT, costs=None):
        self.backend = backend
        self.model = model
        self.effort = effort
        self.costs = costs or SessionCosts()
        self.history = []      # the messages sent to the API
        self.transcript = []   # what the tab shows and the export writes

    def request(self, tools):
        params = {'model': self.model, 'max_tokens': MAX_TOKENS, 'system': SYSTEM_PROMPT, 'tools': toolDefinitions(tools),
                  'messages': self.history, 'output_config': {'effort': self.effort}, 'cache_control': {'type': 'ephemeral'},
                  'betas': []}
        if self.model in FALLBACK_MODELS:
            params['betas'].append(FALLBACK_BETA)
            params['fallbacks'] = 'default'
        return params

    def ask(self, question, context, tools, run_tool, callbacks):
        """one question until the answer ends; tools: the allowed registry entries; run_tool(name, input) -> (result, is_error)"""
        allowed = {t['name'] for t in tools}
        self.history.append({'role': 'user', 'content': [{'type': 'text', 'text': '{}\n\n{}'.format(context, question)}]})
        self.transcript.append({'role': 'user', 'text': question, 'context': context})
        self.costs.startAnswer()
        while True:
            if callbacks.stopped():
                return self.end(callbacks, 'stopped by the user')
            if self.costs.overLimit():
                if not callbacks.confirmContinue(self.costs):
                    return self.end(callbacks, 'stopped at the cost limit of the session ({:.2f} USD)'.format(self.costs.limit))
                self.costs.raiseLimit()
            message = self.backend.step(self.request(tools), callbacks.text)
            self.costs.add(getattr(message, 'model', self.model), getattr(message, 'usage', None), self.model)
            callbacks.cost(self.costs)
            self.history.append({'role': 'assistant', 'content': message.content})
            for block in message.content:
                if blockType(block) == 'fallback':
                    callbacks.note('{} declined, {} continued'.format(getattr(getattr(block, 'from_', None), 'model', '?'),
                                                                     getattr(getattr(block, 'to', None), 'model', '?')))
            text = blockText(message.content)
            if text:
                self.transcript.append({'role': 'assistant', 'text': text})
            reason = message.stop_reason
            tool_uses = [b for b in message.content if blockType(b) == 'tool_use']
            if reason == 'pause_turn':
                continue
            if reason == 'refusal':
                details = getattr(message, 'stop_details', None)
                category = getattr(details, 'category', None) if details else None
                return self.end(callbacks, 'the model declined this request (category: {})'.format(category or 'none'), tool_uses)
            if reason == 'max_tokens':
                return self.end(callbacks, 'the answer reached its maximum length', tool_uses)
            if reason != 'tool_use' or not tool_uses:
                return 'end_turn'
            results = []
            for block in tool_uses:
                entry = {'role': 'tool', 'name': block.name, 'input': block.input}
                if block.name not in allowed:
                    result, is_error = 'not allowed in this project', True
                else:
                    result, is_error = run_tool(block.name, block.input)
                entry.update(result=result, is_error=is_error)
                self.transcript.append(entry)
                callbacks.tool(entry)
                content = [{'type': 'text', 'text': str(result)}] if is_error else resultContent(result)
                results.append({'type': 'tool_result', 'tool_use_id': block.id, 'content': content, 'is_error': bool(is_error)})
            # all results of one assistant turn in one message
            self.history.append({'role': 'user', 'content': results})

    def end(self, callbacks, text, open_tool_uses=()):
        """a note in the chat; tool calls of the last turn that will not run get an error result, so the history stays
        valid for the next question"""
        if open_tool_uses:
            self.history.append({'role': 'user', 'content': [
                {'type': 'tool_result', 'tool_use_id': b.id, 'content': [{'type': 'text', 'text': 'not run: ' + text}], 'is_error': True}
                for b in open_tool_uses]})
        self.transcript.append({'role': 'note', 'text': text})
        callbacks.note(text)
        return text


class AnthropicBackend:
    """one streamed request of the SDK (beta endpoint for the refusal fallback); text arrives while it is generated"""

    def __init__(self, client):
        self.client = client

    def step(self, params, on_text):
        params = dict(params)
        if not params.get('betas'):
            params.pop('betas', None)
        with self.client.beta.messages.stream(**params) as stream:
            for event in stream:
                if getattr(event, 'type', None) == 'text':
                    on_text(event.text)
            return stream.get_final_message()


def errorText(error, key_source):
    """the chat's message for an SDK error, most specific first"""
    import anthropic
    source = {'settings': 'the key of the QGIS settings', 'environment': 'ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN',
              'profile': 'the ant login profile'}.get(key_source, 'no key')
    if isinstance(error, anthropic.AuthenticationError):
        return 'The API key was rejected ({}). Enter a valid key in the Districts Modeler settings.'.format(source)
    if isinstance(error, anthropic.PermissionDeniedError):
        return 'The API key has no access to this model ({}).'.format(source)
    if isinstance(error, anthropic.RateLimitError):
        return 'Rate limit of the API reached; try again in a moment.'
    if isinstance(error, anthropic.APIStatusError):
        return 'API error {}: {}'.format(error.status_code, error.message)
    if isinstance(error, anthropic.APIConnectionError):
        return 'No connection to the Claude API (internet, proxy or firewall).'
    if key_source is None:
        return NO_KEY_TEXT
    return '{}: {}'.format(type(error).__name__, error)
