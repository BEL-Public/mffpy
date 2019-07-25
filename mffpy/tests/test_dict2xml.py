
from ..dict2xml import dict2xml, TEXT, ATTR


def test_dict2xml():
    rootname = 'myroot'
    content = {
        'a': {TEXT: '35', ATTR: {'hello': 'world'}},
        'b': [{TEXT: 'b' + str(i+1)} for i in range(2)]
    }
    elem = dict2xml(content, rootname=rootname)
    elem.write('test.xml')
    root = elem.getroot()
    a = root.find('a')
    bs = root.findall('b')
    assert root.tag == 'myroot', root.tag
    assert a.tag == 'a', a.tag
    assert a.text == '35', a.text
    assert a.get('hello') == 'world'
    for i, b in enumerate(bs):
        assert b.text == 'b' + str(i + 1)
