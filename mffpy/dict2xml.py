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
import xml.etree.ElementTree as ET
from typing import Dict, List, Union

__all__ = [
    'dict2xml',
    'TEXT',
    'ATTR'
]


def register_namespace(ns, tag=''):
    """register namespace prefix `ns` for tag `tag`"""
    ET.register_namespace(tag, ns)


# key `TEXT` indicates innerXML
TEXT = 'text'
# key `ATTR` indicates an XML attribute
ATTR = 'attributes'


def dict2el(tag: str, content: dict, el: ET.Element,
            namespace: str = '') -> None:
    attrs = content.pop(ATTR, {})
    assert isinstance(attrs, dict), f"""
    Attributes have to be dict.  Got {attrs}."""
    text = content.pop(TEXT, '')
    subel = ET.SubElement(el, namespace+tag, **attrs)
    if isinstance(text, str):
        subel.text = text
    elif isinstance(text, dict):
        for subtag, inside in text.items():
            add2el(subtag, inside, subel)
    else:
        raise AttributeError(f"inside of <{tag}> has unknown format [{text}]")


def add2el(tag: str, content: Union[dict, List[dict]],
           el: ET.Element, namespace: str = '') -> None:
    if isinstance(content, dict):
        dict2el(tag, content, el, namespace)
    elif isinstance(content, list):
        for c in content:
            dict2el(tag, c, el, namespace)
    else:
        raise AttributeError(
            f"inside of <{tag}> has unknown format [{content}]")


def dict2xml(content: Dict[str, Union[Dict, List]], rootname: str = 'root',
             namespace: str = '') -> ET.ElementTree:
    kwargs = {
        'xmlns': namespace,
        'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }
    root = ET.Element(rootname, **kwargs)  # type: ignore
    for tag, inside in content.items():
        add2el(tag, inside, root)

    return ET.ElementTree(root)
