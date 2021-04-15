import logging

import docs_parser


log = logging.getLogger()

if __name__ == '__main__':
    with open("input/input.html") as f:
        content = f.readlines()
    content = "".join([str(line) for line in content])

    docs_parser.run(content)
