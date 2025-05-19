from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Single-character tokens.
    LEFT_SQUARE_BRACKET = auto()
    RIGHT_SQUARE_BRACKET = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    COLON = auto()
    QUOTES = auto()

    # Literals.
    STRING = auto()
    NUMBER = auto()

    # Keywords.
    NULL = auto()
    FALSE = auto()
    TRUE = auto()
    NAN = auto()
    INFINITY = auto()
    MINUS_INFINITY = auto()

    # Unparsable.
    GARBAGE = auto()

    EOF = auto()


KEYWORDS = {
    "null": TokenType.NULL,
    "false": TokenType.FALSE,
    "true": TokenType.TRUE,
    "NaN": TokenType.NAN,
    "Infinity": TokenType.INFINITY,
}

SIGNED_KEYWORDS = {
    "+": {"NaN": TokenType.NAN, "Infinity": TokenType.INFINITY,},
    "-": {"NaN": TokenType.NAN, "Infinity": TokenType.MINUS_INFINITY,},
}

CHAR_TOKENS = {
    "[": TokenType.LEFT_SQUARE_BRACKET,
    "]": TokenType.RIGHT_SQUARE_BRACKET,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    ",": TokenType.COMMA,
    ":": TokenType.COLON,
    '"': TokenType.QUOTES,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: object
    start: int
    line: int
    column: int


class Scanner:
    def __init__(self, source):
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1
        self.line_start = 0
        self.garbage = False

    def next(self):
        while True:
            token = self._scan_token()
            if token.type == TokenType.GARBAGE:
                if self.garbage:
                    # absorb sequences of garbage into a single token
                    continue
                self.garbage = True
            else:
                self.garbage = False
            break
        return token

    def _is_at_end(self):
        return self.current >= len(self.source)

    def _scan_token(self):
        while True:
            self.start = self.current
            if self._is_at_end():
                return self._new_token(TokenType.EOF)
            c = self._advance()
            if c in CHAR_TOKENS:
                return self._new_token(CHAR_TOKENS[c])
            elif c in "+-":
                if self._peek().isdigit():
                    return self._number()
                elif self._peek().isalpha():
                    return self._keyword(c)
                else:
                    return self._new_token(TokenType.GARBAGE)
            elif c == "/" and self._match("/"):
                self._comment()
            elif c in " \r\t":
                pass
            elif c == "\n":
                self.line += 1
                self.line_start = self.current
            elif c.isdigit():
                return self._number()
            elif c.isalpha():
                return self._keyword()
            else:
                return self._new_token(TokenType.GARBAGE)

    @property
    def column(self):
        return self.current - self.line_start

    def _advance(self):
        self.current += 1
        return self.source[self.current - 1]

    def _new_token(self, type, literal=None):
        text = self.source[self.start : self.current]
        return Token(type, text, literal, self.start, self.line, self.column)

    def _match(self, expected):
        if self._peek() == expected:
            self._advance()
            return True
        else:
            return False

    def _peek(self, lookahead=1):
        pos = self.current + lookahead - 1
        if pos >= len(self.source):
            return "\0"
        return self.source[pos]

    def _number(self):
        while self._peek().isdigit():
            self._advance()

        is_int = True
        if self._peek() == "." and self._peek(2).isdigit():
            is_int = False
            # consume separator
            self._advance()
            while self._peek().isdigit():
                self._advance()

        if self._peek() in "eE" and (
            (self._peek(2) in "-+" and self._peek(3).isdigit())
            or self._peek(2).isdigit()
        ):
            is_int = False
            # consume e
            self._advance()
            # consume sign
            if self._peek() in "+-":
                self._advance()
            while self._peek().isdigit():
                self._advance()

        text = self.source[self.start : self.current]
        if is_int:
            value = int(text)
        else:
            value = float(text)

        return self._new_token(TokenType.NUMBER, value)

    def _keyword(self, sign=""):
        while self._peek().isalpha():
            self._advance()

        name = self.source[self.start + len(sign) : self.current]
        if sign:
            keywords = SIGNED_KEYWORDS[sign]
        else:
            keywords = KEYWORDS
        try:
            type = keywords[name]
        except KeyError:
            type = TokenType.GARBAGE
        return self._new_token(type)

    def _comment(self):
        while self._peek() != "\n" and not self._is_at_end():
            self._advance()


class StringScanner:
    def __init__(self, source, start=0, line=1):
        self.source = source
        self.chars = []
        self.current = start
        self.start = start
        self.line = line

    def scan_string(self):
        try:
            while not self._scan_char():
                pass
        except IndexError:
            self._error("Unexpected end of stream while processing string")
        text = self.source[self.start - 1 : self.current]
        value = "".join(self.chars)
        token = Token(TokenType.STRING, text, value, self.start, self.line, self.start)
        return token

    def _is_at_end(self):
        return self.current >= len(self.source)

    def _scan_char(self):
        c = self._advance()
        if c == "\\":
            c = self._advance()
            if c in '"\\/':
                self.chars.append(c)
            elif c == "b":
                self.chars.append("\b")
            elif c == "f":
                self.chars.append("\f")
            elif c == "n":
                self.chars.append("\n")
            elif c == "r":
                self.chars.append("\r")
            elif c == "t":
                self.chars.append("\t")
            elif c == "u":
                hexcode = "".join(self._advance() for _ in range(4))
                self.chars.append(chr(int(hexcode, 16)))
            else:
                self.chars.append(c)
        elif c == "\n":
            self._error("Unexpected line end while processing string")
        elif c == '"':
            return True
        else:
            self.chars.append(c)
        return False

    def _advance(self):
        self.current += 1
        return self.source[self.current - 1]

    def _error(self, message):
        raise StringScanError(message, self.start)


class StringScanError(Exception):
    def __init__(self, message, restart_position):
        super().__init__(message)
        self.restart_position = restart_position
