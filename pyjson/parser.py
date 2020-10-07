from .scanner import TokenType, StringScanner, StringScanError


class Handler:
    def reset(self):
        pass

    def start_object(self):
        pass

    def end_object(self):
        pass

    def start_array(self):
        pass

    def end_array(self):
        pass

    def property(self, name):
        pass

    def element(self, value):
        pass


class BuildObjectHandler:
    def __init__(self):
        self.top_level = []
        self.reset()

    def reset(self):
        # print("reset")
        self.stack = []

    def start_object(self):
        # print("start_object")
        self.stack.append({})

    def end_object(self):
        # print("end_object")
        self.element(self.stack.pop())

    def start_array(self):
        # print("start_array")
        self.stack.append([])

    def end_array(self):
        # print("end_array")
        self.element(self.stack.pop())

    def property(self, name):
        # print("property", name)
        self.stack.append(name)

    def element(self, value):
        # print("element", value)
        if not self.stack:
            # must be top-level element
            self.top_level.append(value)
        elif isinstance(self.stack[-1], str):
            # must be an object
            property_name = self.stack.pop()
            self.stack[-1][property_name] = value
        elif isinstance(self.stack[-1], list):
            # must be an array
            self.stack[-1].append(value)
        else:
            assert False, "not reachable"


class Parser:
    def __init__(self, scanner, handler):
        self.scanner = scanner
        self.previous = None
        self.current = scanner.next()
        self.handler: Handler = handler

    def parse(self):
        self.json()

    def json(self):
        while not self.is_at_end():
            try:
                self.broken_document()
            except ParseError:
                self.reset()

    def broken_document(self):
        if self.match(TokenType.LEFT_SQUARE_BRACKET):
            self.list()
        if self.match(TokenType.LEFT_BRACE):
            self.object()
        self.error(self.peek(), "Expected object or array.")

    def element(self):
        if self.match(TokenType.LEFT_SQUARE_BRACKET):
            return self.list()
        elif self.match(TokenType.LEFT_BRACE):
            return self.object()
        elif self.match(TokenType.QUOTES):
            return self.string()
        elif self.match(TokenType.NUMBER):
            self.handler.element(self.previous.literal)
        elif self.match(TokenType.TRUE):
            self.handler.element(True)
        elif self.match(TokenType.FALSE):
            self.handler.element(False)
        elif self.match(TokenType.NULL):
            self.handler.element(None)
        elif self.match(TokenType.NAN):
            self.handler.element(float("nan"))
        elif self.match(TokenType.INFINITY):
            self.handler.element(float("+inf"))
        elif self.match(TokenType.MINUS_INFINITY):
            self.handler.element(float("-inf"))
        else:
            self.error(self.peek(), "Expected JSON element.")

    def list(self):
        self.handler.start_array()
        while True:
            if self.check(TokenType.RIGHT_SQUARE_BRACKET):
                break
            self.element()
            if not self.match(TokenType.COMMA):
                break
        self.consume(TokenType.RIGHT_SQUARE_BRACKET, "Expected ']' at end of list.")
        self.handler.end_array()

    def object(self):
        self.handler.start_object()
        while True:
            if self.check(TokenType.RIGHT_BRACE):
                break
            self.property()
            if not self.match(TokenType.COMMA):
                break
        self.consume(TokenType.RIGHT_BRACE, "Expected ']' at end of list.")
        self.handler.end_object()

    def property(self):
        quotes = self.consume(TokenType.QUOTES, "Expected property name.")
        try:
            property_name = self._get_string().literal
            self.consume(TokenType.COLON, "Expected ':' after property name.")
        except (ParseError, StringScanError):
            self.scanner.current = quotes.start + 1
            raise
        self.handler.property(property_name)
        self.element()

    def string(self):
        quotes = self.previous
        value = self._get_string()
        if not self.check(
            TokenType.COMMA, TokenType.RIGHT_SQUARE_BRACKET, TokenType.RIGHT_BRACE
        ):
            self.scanner.current = quotes.start + 1
            self.error("Cannot continue after string")
        self.handler.element(value.literal)

    def _get_string(self):
        token = self.previous
        string_scanner = StringScanner(self.scanner.source, token.start + 1, token.line)
        try:
            value = string_scanner.scan_string()
        except StringScanError:
            self.error(token, "Invalid string")
        else:
            self.scanner.current = string_scanner.current
            self.advance()
            return value

    def match(self, *types):
        if any(map(self.check, types)):
            self.advance()
            return True
        return False

    def check(self, *types):
        if self.is_at_end():
            return False
        return self.peek().type in types

    def advance(self):
        if not self.is_at_end():
            self.previous = self.current
            self.current = self.scanner.next()
        return self.previous

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.current

    def consume(self, type, message):
        if self.check(type):
            return self.advance()
        self.error(self.peek(), message)

    def error(self, token, message):
        raise ParseError

    def reset(self):
        self.handler.reset()
        while not self.is_at_end():
            if self.peek().type in (
                TokenType.LEFT_SQUARE_BRACKET,
                TokenType.LEFT_BRACE,
            ):
                return

            self.advance()


class ParseError(Exception):
    pass
