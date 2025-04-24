from typing import List


def lexer(code: str) -> List[str | int]:
    tokens = []
    i = 0
    while i < len(code):
        char = code[i]
        if char in "\n\t\r ":
            i += 1
            continue
        if char == '"':
            value = ""
            i += 1
            while i < len(code) and code[i] != '"':
                if code[i] == "\\":
                    i += 1
                    match code[i]:
                        case '"':
                            value += '\\"'
                        case '\'':
                            value += '\\\''
                        case '\\':
                            value += '\\\\'
                        case 'n':
                            value += '\\n'
                        case 't':
                            value += '\\t'
                        case 'b':
                            value += '\\b'
                        case 'e':
                            value += '\\x1b'
                        case 'r':
                            value += '\\r'
                else:            
                    value += code[i]
                i += 1
            i += 1
            tokens.append('"' + value + '"')
            continue
        if char == '\'':
            value = ""
            i += 1
            while i < len(code) and code[i] != '\'':
                if code[i] == "\\":
                    i += 1
                    match code[i]:
                        case '"':
                            value += '\\"'
                        case '\'':
                            value += '\\\''
                        case '\\':
                            value += '\\\\'
                        case 'n':
                            value += '\\n'
                        case 't':
                            value += '\\t'
                        case 'b':
                            value += '\\b'
                        case 'e':
                            value += '\\x1b'
                        case 'r':
                            value += '\\r'
                else:            
                    value += code[i]
                i += 1
            i += 1
            tokens.append('\'' + value + '\'')
            continue
        if char in "!@#$%^&*()-=_+[]{};:'|\\/?.,><":
            c = char
            if char in "-+*/%<>=" and code[i + 1] == '=':
                c += '='
                i += 1
            tokens.append(c)
            i += 1
            continue
        if char.isdigit():
            value = ""
            while i < len(code) and code[i].isdigit():
                value += code[i]
                i += 1
            tokens.append(int(value))
            continue
        if char.isalpha() or char == '_':
            value = ""
            while i < len(code) and (code[i].isalpha() or code[i] == '_' or code[i].isdigit()):
                value += code[i]
                i += 1
            tokens.append(value)
            continue
    return tokens