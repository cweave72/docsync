import re
import logging
import os.path as osp

from typing import Tuple, Union, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

DIRNAME = osp.abspath(osp.dirname(__file__))

func_re = re.compile(r"""
    /\*+                                     # Match opening /***************
    \s+\[(?:docimport|docexport)\s+\w*\]\s+  # Match the [docimport funcname] line
    \*//\*\*                                 # Match the token *//**
    .*?                                      # Everything else withing the docstring.
    \*+/\n                                   # Match the closing ************/
    \w+ \s* [*]? \s* (?P<name>\w+) \(.*?\);?  # Match the function signature
""", re.VERBOSE | re.DOTALL)


@dataclass
class Func:
    """Encapsulates a matched function withing the text string.
    """
    name: str
    span: Tuple[int, int]
    substring: str


class Docsync:
    """Class which provides the docsync functionality.
    """

    def __init__(self):
        self.start = None
        self.end = None

    def search(self, text: str) -> int:
        """ Searches through source text and extract function docstring and
        prototype.
        Returns the number of matches found.
        """
        match = None
        self.funcs = []
        for match in func_re.finditer(text):
            if self.start is None:
                # Get the string index of the start of matches.
                self.start = match.span()[0]
                logger.debug(f"start={self.start}")
            f = Func(match.group('name'),
                     match.span(),
                     match.group(0))
            logger.debug(f"Found function: {f.name}")
            self.funcs.append(f)

        # Get the end index of matches.
        if match:
            self.end = match.span()[1]
            logger.debug(f"end={self.end}")

        return len(self.funcs)

    def _index_str(self, text: str) -> Dict[int, Tuple[int, str]]:
        """Indexes a supplied string. Provides a dict with keys corresponding
        to string index of the beginning of each line.
        {string_index: (line_number, line text)}.
        """
        lines = text.split('\n')
        index_dict = {}
        index_count = 0
        for line_num, line in enumerate(lines):
            index_dict[index_count] = (line_num, line)
            logger.debug(f"index entry = {index_count}: {line_num}, {line}")
            index_count += len(line) + 1  # Add 1 to account for line-feed

        return index_dict

    def search_hdr(self, text: str) -> Tuple[int, int]:
        """Searches header string for insertion point of docexport text.
        Returns the line index replacement range for header text insertion.
        Similar to an array slice, the end index is exclusive
        (i.e. [start, end) ).
        If no matches are found, 0, 0 is returned.
        """
        # Search for matches in the text.
        num = self.search(text)

        # Index the supplied string.
        index_dict = self._index_str(text)

        line_start = 0
        line_end = 0

        if num != 0:
            line_start, _ = index_dict.get(self.start, (0, 0))
            line_end, _ = index_dict.get(self.end+1, (0, 0))
            logger.debug(f"Header replacement lines: start={line_start}; end={line_end}")
            return line_start, line_end

        logger.debug("No matches found, searching for closing #endif.")
        lines = text.split('\n')
        line_num = len(lines) - 1
        for line in lines[::-1]:
            if line.startswith("#endif"):
                logger.debug(f"Found #endif at line index {line_num}. "
                             f"Insert header at line {line_num-1}")
                return (line_num - 1, line_num - 1)
                break
            line_num -= 1
        else:
            logger.debug("Closing #endif not found.")
            return 0, 0

    def docexport(self, output_type: str = "lines") -> Union[str, List[str]]:
        """Dumps the docexport string for insertion into header.
        Returns the output as a string or list of lines.
        """
        out = []
        for item in self.funcs:
            docexport_str = item.substring.replace("docimport", "docexport") + ';'
            out.append(docexport_str)

        joined = "\n\n".join(out)

        if output_type == "lines":
            # Return as a list of lines.
            return joined.split('\n')

        # Default to returning the joined string.
        return "\n\n".join(out)
