# coding=utf-8
"""Guidance of the AI connection (OpenSpec change ai-mcp-connection, spec ai-guidance): the workflow map, the wiki URLs,
the error without network; online: every mapped page exists and the search finds the sizing page.

    python -m pytest test/test_mcp_guidance.py -v          (-m "not online" without internet)
"""
import pytest

from districts.mcp import guidance
from districts.utility_functions.model_checks import RULE_IDS


def mapped_pages():
    return sorted({p for s in guidance.loadMap()['steps'] if s['wiki'] != 'missing' for p in s['wiki']})


def test_map_names_existing_rules_and_unique_steps():
    steps = guidance.loadMap()['steps']
    assert len({s['step'] for s in steps}) == len(steps)
    unknown = sorted({r for s in steps for r in s['rules']} - set(RULE_IDS))
    assert not unknown, 'rules of wiki_map.json that model_checks.py does not have: {}'.format(unknown)
    for s in steps:
        assert s['wiki'] == 'missing' or all(p.startswith('IDA_Districts.') for p in s['wiki']), s['step']


def test_new_features_are_marked_missing():
    steps = {s['step']: s for s in guidance.loadMap()['steps']}
    for name in ('cost_optimization', 'representative_periods', 'economics', 'energy_use', 'network_pumps', 'pipe_series', 'dynamic_sizing'):
        assert steps[name]['wiki'] == 'missing', name


def test_urls():
    data = guidance.loadMap()
    page = 'IDA_Districts.Districts_GS.Districts_Modeler_GS.Sizing_network.WebHome'
    assert guidance.pageUrl(data, page) == 'https://equa.cloud.xwiki.com/xwiki/bin/view/IDA_Districts/Districts_GS/Districts_Modeler_GS/Sizing_network/'
    assert guidance.restUrl(data, page) == ('https://equa.cloud.xwiki.com/xwiki/rest/wikis/xwiki/spaces/IDA_Districts/spaces/Districts_GS/'
                                            'spaces/Districts_Modeler_GS/spaces/Sizing_network/pages/WebHome?media=json')
    with pytest.raises(ValueError):
        guidance.splitPage('WebHome')


def test_only_pages_of_the_space():
    with pytest.raises(guidance.WikiError, match='only pages of the space'):
        guidance.readHelpPage('XWiki.XWikiPreferences.WebHome')


def test_wiki_unreachable(monkeypatch):
    data = dict(guidance.loadMap(), base_url='http://127.0.0.1:9/xwiki')
    monkeypatch.setattr(guidance, 'loadMap', lambda: data)
    monkeypatch.setattr(guidance, 'TIMEOUT_S', 2)
    with pytest.raises(guidance.WikiError, match='wiki unreachable'):
        guidance.searchHelp('pipe sizing')


@pytest.fixture
def online():
    try:
        guidance.searchHelp('IDA Districts', 1)
    except guidance.WikiError as e:
        pytest.skip('wiki not reachable: {}'.format(e))


@pytest.mark.online
def test_mapped_pages_exist(online):
    missing = []
    for page in mapped_pages():
        try:
            assert guidance.readHelpPage(page)['content'] is not None
        except guidance.WikiError as e:
            missing.append('{} ({})'.format(page, e))
    assert not missing, 'wiki pages of wiki_map.json not found:\n' + '\n'.join(missing)


@pytest.mark.online
def test_search_finds_the_sizing_page(online):
    pages = [r['page'] for r in guidance.searchHelp('pipe sizing')['results']]
    assert 'IDA_Districts.Districts_GS.Districts_Modeler_GS.Sizing_network.WebHome' in pages
    assert all(p.startswith('IDA_Districts.') for p in pages)
