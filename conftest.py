def pytest_addoption(parser):
    parser.addoption(
        '--xml-backend',
        default='lxml',
        choices=['lxml', 'defusedxml'],
        help='XML parsing backend to use (default: lxml)',
    )
