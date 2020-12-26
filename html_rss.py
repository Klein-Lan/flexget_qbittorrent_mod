from urllib.parse import urljoin

import chardet
from flexget import plugin
from flexget.entry import Entry
from flexget.event import event
from flexget.utils.soup import get_soup
from loguru import logger
from requests import RequestException


class PluginHtmlRss():
    schema = {
        'type': 'object',
        'properties': {
            'url': {'type': 'string', 'format': 'url'},
            'headers': {
                'type': 'object',
                'properties': {
                    'cookie': {'type': 'string'},
                    'user-agent': {'type': 'string'},
                }
            },
            'params': {'type': 'string'},
            "root_element_selector": {'type': 'string'},
            'fields': {
                'type': 'object',
                'properties': {
                    'title': {
                        'type': 'object',
                        'properties': {
                            'element_selector': {'type': 'string'},
                            'attribute': {'type': 'string'},
                        }
                    },
                    'url': {
                        'type': 'object',
                        'properties': {
                            'element_selector': {'type': 'string'},
                            'attribute': {'type': 'string'},
                        },
                    }
                },
                'required': ['title', 'url'],
            }
        },
        'required': ['url'],
        'additionalProperties': False
    }

    def prepare_config(self, config):
        config.setdefault('url', '')
        config.setdefault('headers', {})
        config.setdefault('params', '')
        config.setdefault('root_element_selector', '')
        config.setdefault('fields', {})
        return config

    def on_task_input(self, task, config):
        config = self.prepare_config(config)
        url = config.get('url')
        root_element_selector = config.get('root_element_selector')
        fields = config.get('fields')
        params = config.get('params')

        entries = []
        elements = []
        if url and root_element_selector:
            try:
                if brotli:
                    config.get('headers')['accept-encoding'] = 'gzip, deflate, br'
                response = task.requests.get(url, headers=config.get('headers'), timeout=60)
                content = self._decode(response)
            except RequestException as e:
                raise plugin.PluginError(
                    'Unable to download the Html for task {} ({}): {}'.format(task.name, url, e)
                )
            elements = get_soup(content).select(root_element_selector)
            if len(elements) == 0:
                return entries

        for element in elements:
            logger.debug('element in element_selector: {}', element)
            entry = Entry()
            for key, value in fields.items():
                entry[key] = ''
                sub_element = element.select_one(value['element_selector'])
                if sub_element:
                    if value['attribute'] == 'textContent':
                        sub_element_content = sub_element.get_text()
                    else:
                        sub_element_content = sub_element.get(value['attribute'], '')
                    entry[key] = sub_element_content
                logger.debug('key: {}, value: {}', key, entry[key])
            if entry['title'] and entry['url']:
                base_url = urljoin(url, entry['url'])
                if params.startswith("&"):
                    entry['url'] = base_url + params
                else:
                    entry['url'] = urljoin(base_url, params)
                entry['original_url'] = entry['url']
                entries.append(entry)
        return entries

    def _decode(self, response):
        if response is None:
            return None
        content = response.content
        charset_encoding = chardet.detect(content).get('encoding')
        if charset_encoding == 'ascii':
            charset_encoding = 'unicode_escape'
        elif charset_encoding == 'Windows-1254':
            charset_encoding = 'utf-8'
        return content.decode(charset_encoding if charset_encoding else 'utf-8', 'ignore')


@event('plugin.register')
def register_plugin():
    plugin.register(PluginHtmlRss, 'html_rss', api_ver=2)
