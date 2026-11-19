# coding=utf-8
"""Export of a conversation as one HTML file (OpenSpec change ai-chat-panel, D7): questions, answers, tool calls with
their arguments and results (collapsed), model and costs. The API key is never part of a conversation."""
import datetime
import html
import json
import os

from .costs import PRICES_DATE


def exportFileName(now=None):
    return 'ai_chat_{}.html'.format((now or datetime.datetime.now()).strftime('%Y%m%d_%H%M%S'))


def defaultExportPath(config, now=None):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'], exportFileName(now))


def toolResultText(entry):
    if entry.get('is_error'):
        return str(entry.get('result'))
    result = entry.get('result')
    if isinstance(result, dict) and 'image_png_base64' in result:
        return '<img alt="map" src="data:image/png;base64,{}">'.format(result['image_png_base64'])
    from ..mcp.tools import jsonValue
    return '<pre>{}</pre>'.format(html.escape(json.dumps(result, default=jsonValue, ensure_ascii=False, indent=1)))


def conversationHtml(transcript, model, costs, project, version, now=None):
    parts = []
    for entry in transcript:
        role = entry['role']
        if role == 'user':
            parts.append('<div class="user"><b>Question</b><p>{}</p></div>'.format(html.escape(entry['text']).replace('\n', '<br>')))
        elif role == 'assistant':
            parts.append('<div class="assistant"><b>Answer</b><p>{}</p></div>'.format(html.escape(entry['text']).replace('\n', '<br>')))
        elif role == 'tool':
            parts.append('<details class="tool{}"><summary>Tool {} {}</summary>{}</details>'.format(
                ' error' if entry.get('is_error') else '', html.escape(entry['name']),
                html.escape(json.dumps(entry.get('input') or {}, ensure_ascii=False)), toolResultText(entry)))
        else:
            parts.append('<p class="note">{}</p>'.format(html.escape(entry['text'])))
    stamp = (now or datetime.datetime.now()).strftime('%Y-%m-%d %H:%M')
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>AI assistant {project} / {version}</title>
<style>body{{font-family:sans-serif;max-width:60em;margin:2em auto}} .user{{background:#eef3fb;padding:.5em}}
.assistant{{padding:.5em}} details{{margin:.3em 0 .3em 1em;color:#444}} .error summary{{color:#b00}} .note{{color:#777;font-style:italic}}
pre{{white-space:pre-wrap;font-size:85%}} img{{max-width:100%}}</style></head>
<body><h1>AI assistant – {project} / {version}</h1>
<p>{stamp} · model {model} · estimated cost {cost:.2f} USD (prices of {prices})</p>
{body}
</body></html>""".format(project=html.escape(project or ''), version=html.escape(version or ''), stamp=stamp, model=html.escape(model),
                         cost=costs.total, prices=PRICES_DATE, body='\n'.join(parts))


def exportConversation(path, transcript, model, costs, project, version):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(conversationHtml(transcript, model, costs, project, version))
    return path
