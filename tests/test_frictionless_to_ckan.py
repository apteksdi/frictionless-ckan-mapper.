# coding=utf-8
import json

import frictionless_ckan_mapper.frictionless_to_ckan as converter


class TestResourceConversion:
    def test_non_ckan_keys_passthrough(self):
        indict = {
            'title_cn': u'國內生產總值',
            'years': [2015, 2016],
            'last_year': 2016,
            'location': {'country': 'China'}
        }
        out = converter.resource(indict)
        exp = {
            'title_cn': u'國內生產總值',
            'years': [2015, 2016],
            'last_year': 2016,
            'location': {'country': 'China'}
        }
        assert out == exp

    def test_path_to_url(self):
        # Test remote path
        indict = {'path': 'http://www.somewhere.com/data.csv'}
        out = converter.resource(indict)
        assert out['url'] == indict['path']

        # Test local path
        indict = {'path': './data.csv'}
        out = converter.resource(indict)
        assert out['url'] == indict['path']

        # Test POSIX path
        indict = {'path': '/home/user/data.csv'}
        out = converter.resource(indict)
        assert out['url'] == indict['path']

    def test_other_remapping(self):
        indict = {
            'bytes': 10,
            'mediatype': 'text/csv'
        }
        exp = {
            'size': 10,
            'mimetype': 'text/csv'
        }
        out = converter.resource(indict)
        assert out == exp

    def test_passthrough(self):
        indict = {
            'description': 'GDPs list',
            'format': 'CSV',
            'hash': 'e785c0883d7a104330e69aee73d4f235'
        }
        out = converter.resource(indict)
        assert out == indict


class TestPackageConversion:
    def test_passthrough(self):
        indict = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
        }
        out = converter.package(indict)
        assert out['name'] == indict['name']
        assert out['title'] == indict['title']
        assert out['version'] == indict['version']

    def test_basic_mappings(self):
        indict = {
            'description': 'Country, regional and world GDP in current USD.',
            'homepage': 'https://datopian.com'
        }
        exp = {
            'notes': 'Country, regional and world GDP in current USD.',
            'url': 'https://datopian.com'
        }
        out = converter.package(indict)
        assert out == exp

    def test_dataset_license(self):
        indict = {
            'licenses': [{
                'name': 'odc-odbl'
            }]
        }
        exp = {
            'license_id': 'odc-odbl',
            'license_title': None,
            'extras': [
                {
                    'key': 'licenses',
                    'value': json.dumps([{ 'name': 'odc-odbl' }])
                }
            ]
        }
        out = converter.package(indict)
        assert out == exp


        # TODO: reinstate with proper extras support
        '''
        indict = {
            'licenses': [{
                'title': 'Open Data Commons Open Database License',
                'name': 'odc-odbl'
            }]
        }
        exp = {
            'license_id': 'odc-odbl',
            'license_title': 'Open Data Commons Open Database License'
        }
        out = converter.package(indict)
        assert out == exp

        # Finally, what if license*s* are already there...
        indict = {
            'licenses': [
                {
                    'title': 'Open Data Commons Open Database License',
                    'type': 'odc-pddl'
                },
                {
                    'title': 'Creative Commons CC Zero License (cc-zero)',
                    'type': 'cc-zero'
                }
            ]
        }
        exp = {
            'extras': [{
                'licenses': indict['licenses']
            }],
            'license_id': 'odc-pddl',
            'license_title': 'Open Data Commons Open Database License',
        }
        out = converter.package(indict)
        assert out == exp
        '''

    # TODO: get clear on the spelling of the key "organization".
    # It's "organisation" in the JSON schema at
    # https://specs.frictionlessdata.io/schemas/data-package.json
    # while it's "organization" in the page of the specs at
    # https://specs.frictionlessdata.io/data-package/#metadata
    def test_contributors(self):
        indict = {
            'contributors': [
                {
                    'title': 'John Smith'
                }
            ]
        }
        exp = {
            'author': 'John Smith',
            'author_email': None,
            'extras': [
                {
                    'key': 'contributors',
                    'value': json.dumps(indict['contributors'])
                }
            ]
        }
        out = converter.package(indict)
        assert out == exp

        # check maintainer conversion
        indict = {
            'contributors': [
                {
                    'title': 'xyz',
                    'email': 'xyz@abc.com',
                    'organisation': 'xxxxx',
                    'role': 'maintainer'
                }
            ]
        }
        exp = {
            'extras': [{
                'key': 'contributors',
                'value': json.dumps(indict['contributors'])
            }],
            'maintainer': 'xyz',
            'maintainer_email': 'xyz@abc.com'
        }
        out = converter.package(indict)
        assert out == exp

        # Make sure that we also get the correct data when there are multiple
        # contributors
        indict = {
            'contributors': [
                {
                    'title': 'abc',
                    'email': 'abc@abc.com'
                },
                {
                    'title': 'xyz',
                    'email': 'xyz@xyz.com',
                    'role': 'maintainer'
                }
            ]
        }
        exp = {
            'extras': [{
                'key': 'contributors',
                'value': json.dumps(indict['contributors'])
            }],
            'author': 'abc',
            'author_email': 'abc@abc.com',
            'maintainer': 'xyz',
            'maintainer_email': 'xyz@xyz.com'
        }
        out = converter.package(indict)
        assert out == exp

    def test_keywords_converted_to_tags(self):
        keywords = ['economy!!!', 'World Bank']
        indict = {'keywords': keywords}
        out = converter.package(indict)
        assert out.get('tags') == [
            {'name': 'economy'},
            {'name': 'world-bank'},
        ]

    def test_extras_is_converted(self):
        indict = {
            'homepage': 'www.example.com',
            'newdict': {'key1': 'dict_to_jsonify'},
            'newint': 123,
            'newkey': 'new value',
            'newlist': [1, 2, 3, 'string'],
            'title': 'Title here'
        }
        exp = {
            'title': 'Title here',
            'url': 'www.example.com',
            'extras': [
                {
                    'key': 'newdict', 'value': '{"key1": "dict_to_jsonify"}'
                },
                {'key': 'newint', 'value': 123},
                {'key': 'newkey', 'value': 'new value'},
                {'key': 'newlist', 'value': '[1, 2, 3, "string"]'},
            ]
        }
        out = converter.package(indict)
        out['extras'] = sorted(out['extras'], key = lambda i: i['key'])
        assert out == exp