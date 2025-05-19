import pytest

from pyjson.scanner import Scanner, TokenType, StringScanner, StringScanError


numbers_to_test = [
    ("0", 0),
    ("0.0", 0.0),
    ("1", 1),
    ("1.0", 1.0),
    ("1.123456", 1.123456),
    ("1.02e6", 1.02e6),
    ("1e-2", 1e-2),
    ("1.1e-2", 1.1e-2),
    ("1e308", 1e308),
    ("1E-2", 1e-2),
    ("1.1E-2", 1.1e-2),
    ("1E308", 1e308),
]

tokens_to_test = [
    (
        '[ ] { } , : " null false true NaN Infinity +Infinity -Infinity',
        """LEFT_SQUARE_BRACKET RIGHT_SQUARE_BRACKET LEFT_BRACE
        RIGHT_BRACE COMMA COLON QUOTES NULL FALSE
        TRUE NAN INFINITY INFINITY MINUS_INFINITY""",
    ),
    (
        """
        [] // foo
        {} // bar
        """,
        "LEFT_SQUARE_BRACKET RIGHT_SQUARE_BRACKET LEFT_BRACE RIGHT_BRACE",
    ),
    ('garbage { foo "', "GARBAGE LEFT_BRACE GARBAGE QUOTES"),
    ('garbage trash poop { foo "', "GARBAGE LEFT_BRACE GARBAGE QUOTES"),
    ("2ef", "NUMBER GARBAGE"),
    ("2e3f", "NUMBER GARBAGE"),
    (
        """
        {
            "hello": {
                "a": 123,
                "b": "x",
            },
            "foo": ["aa", "bbb", +Infinity, -Infinity, NaN],
            "x": true,
            "y": false,
            "z": null
        }
        """,
        """
        LEFT_BRACE
        QUOTES GARBAGE QUOTES COLON LEFT_BRACE
        QUOTES GARBAGE QUOTES COLON NUMBER COMMA
        QUOTES GARBAGE QUOTES COLON QUOTES GARBAGE QUOTES COMMA
        RIGHT_BRACE COMMA
        QUOTES GARBAGE QUOTES COLON LEFT_SQUARE_BRACKET
            QUOTES GARBAGE QUOTES COMMA
            QUOTES GARBAGE QUOTES COMMA
            INFINITY COMMA
            MINUS_INFINITY COMMA
            NAN
            RIGHT_SQUARE_BRACKET COMMA
        QUOTES GARBAGE QUOTES COLON TRUE COMMA
        QUOTES GARBAGE QUOTES COLON FALSE COMMA
        QUOTES GARBAGE QUOTES COLON NULL
        RIGHT_BRACE
        """,
    ),
]

strings_to_test = [
    ('foo"', "foo"),
    ('"', ""),
    ('hello world"', "hello world"),
    (r'\b"', "\b"),
    (r'\f"', "\f"),
    (r'\n"', "\n"),
    (r'\r"', "\r"),
    (r'\t"', "\t"),
    (r'hello \n world"', "hello \n world"),
    (r'\u2603"', "\u2603"),
    (r'aa\u2603"', "aa\u2603"),
    (r'\u2603bb"', "\u2603bb"),
]

failing_strings = [
    "", "foo", "foo\n\"", "5e6+"
]


@pytest.fixture
def expected_tokens(expected_stream):
    return [getattr(TokenType, type) for type in expected_stream.split()]


@pytest.fixture
def scanner(source):
    scanner = Scanner(source)
    yield scanner


@pytest.fixture
def string_scanner(source):
    scanner = StringScanner(source)
    yield scanner


@pytest.mark.parametrize("source,expected_stream", tokens_to_test)
class TestScannerTokens:
    def test_parse(self, scanner, expected_stream):
        scanner.next()

    def test_parse_stream(self, scanner, expected_stream):
        token = None
        while not token or token.type == TokenType.EOF:
            token = scanner.next()

    def test_scanner(self, scanner, expected_tokens):
        stream = []
        while True:
            stream.append(scanner.next())
            if stream[-1].type == TokenType.EOF:
                break
        *tokens, eof = stream
        assert eof.type == TokenType.EOF
        assert [token.type for token in tokens] == expected_tokens


@pytest.mark.parametrize("source,expected", numbers_to_test)
def test_scan_numbers(scanner, expected):
    token = scanner.next()
    assert token.type == TokenType.NUMBER
    assert token.literal == expected


@pytest.mark.parametrize("source,expected", strings_to_test)
def test_string_scanner(string_scanner, expected):
    token = string_scanner.scan_string()
    assert token.type == TokenType.STRING
    assert token.literal == expected


@pytest.mark.parametrize("source", failing_strings)
def test_string_scanner_error(string_scanner):
    with pytest.raises(StringScanError) as error:
        string_scanner.scan_string()
    assert error.value.restart_position == 0
