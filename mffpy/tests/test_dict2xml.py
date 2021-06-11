"""
Copyright 2019 Brain Electrophysiology Laboratory Company LLC

Licensed under the ApacheLicense, Version 2.0(the "License");
you may not use this module except in compliance with the License.
You may obtain a copy of the License at:

http: // www.apache.org / licenses / LICENSE - 2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
ANY KIND, either express or implied.
"""
from os.path import join

from ..dict2xml import dict2xml, TEXT, ATTR


def test_dict2xml(tmpdir):
    rootname = 'myroot'
    content = {
        'a': {TEXT: '35', ATTR: {'hello': 'world'}},
        'b': [{TEXT: 'b' + str(i+1)} for i in range(2)]
    }
    elem = dict2xml(content, rootname=rootname)
    elem.write(join(str(tmpdir), 'test.xml'))
    root = elem.getroot()
    a = root.find('a')
    bs = root.findall('b')
    assert root.tag == 'myroot', root.tag
    assert a.tag == 'a', a.tag
    assert a.text == '35', a.text
    assert a.get('hello') == 'world'
    for i, b in enumerate(bs):
        assert b.text == 'b' + str(i + 1)
