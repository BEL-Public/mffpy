
from ..dict2xml import dict2xml, TEXT, ATTR


def test_dict2xml():
    rootname = 'myroot'
    content = {
        'a': {
            TEXT: '35',
            ATTR: {
                'hello': 'world'
            }
        }
    }
    elem = dict2xml(content, rootname=rootname)
    root = elem.getroot()
    a = root.find('a')
    assert root.tag == 'myroot', root.tag
    assert a.tag == 'a', a.tag
    assert a.text == '35', a.text
    assert a.get('hello') == 'world'
