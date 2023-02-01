import logging
import vim

from typing import List, Union, Any
from pathlib import Path

from docsync.docsync import Docsync

logger = logging.getLogger('docsync')
logger.addHandler(logging.NullHandler())

loglevel = {
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


class DocsyncPlugin:

    def __init__(self):
        self.logging_initialized = False

    def setup_logging(self):
        """Setup plugin logging.
        """
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler('docsync.log', mode='w')
        fmt = logging.Formatter(
            fmt="%(asctime)s: [%(levelname)-6s] %(name)s <%(filename)s:%(lineno)d>: %(message)s")

        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        fmt = logging.Formatter(fmt="[%(levelname)-6s] %(name)s: %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        self.streamHandler = ch
        self.logging_initialized = True

        #import logging_tree; logging_tree.printout()

    def set_logging_level(self):
        if self.logging_enable == 1:
            if not self.logging_initialized:
                self.setup_logging()

            level = loglevel.get(vim.eval('g:Docsync_loglevel'), "error")
            self.streamHandler.setLevel(level)

    def run(self):
        """Entrypoint into the plugin.
        """
        self.logging_enable = int(vim.eval('g:Docsync_enable_logging'))
        self.set_logging_level()

        # Get the current buffer information.
        buffer_num = vim.eval("bufnr('%')")
        self.source_buf = vim.buffers[int(buffer_num)]

        logger.debug(f"Docsync running. Got buffer number "
                     f"{self.source_buf.number}: {self.source_buf.name}")

        self.filepath = Path(self.source_buf.name)
        self.dir = self.filepath.parent
        self.basename = self.filepath.stem
        ext = self.filepath.suffix

        if ext != ".c":
            logger.error(f"Docsync: Not a C file ({ext}).")
            return

        header_buf = self.get_header_buffer()
        if header_buf is None:
            # Didn't find header in buffer list. Search for it.
            header_path = self.header_fs_search()
            if header_path is None:
                return
            # Load it into a buffer.
            self.open_file(header_path)

            # Get the lines from the loaded buffer.
            header_buf = self.get_header_buffer()
            if header_buf is None:
                return

        logger.debug(f"Found header buffer: {header_buf.number} "
                     f"{header_buf.name}")
        self.header_buf = header_buf

        # At this point, we have the source buffer and the header buffer.
        # Ready to sync.
        self.sync()

    def sync(self):
        """Does the work.
        """
        # Get source as a string.
        source_str = "\n".join(self.source_buf[:])
        # Parse the source for function docstrings and signatures.
        logger.debug(f"Searching source file {self.filepath.name}")
        source_sync = Docsync()
        source_sync.search(source_str)
        # Get the list of lines to be exported to the header (i.e. overwrite
        # function prototypes in the header buffer).
        export_lines = source_sync.docexport()

        # Get header as a string.
        header_str = "\n".join(self.header_buf[:])
        # Parse header to find the range of lines to replace.
        logger.debug("Searching header file.")
        header_sync = Docsync()
        hdr_start, hdr_end = header_sync.search_hdr(header_str)

        # Delete the lines in the header buffer.
        self.header_buf[hdr_start:hdr_end] = None
        header_lines = self.header_buf[:]
        # Insert lines into header.
        header_lines = header_lines[:-1] + export_lines + [header_lines[-1]]
        self.header_buf[:] = header_lines

    def get_header_buffer(self) -> Union[Any, None]:
        """Searches for the header file in tha buffer list and returns
        the buffer, if found.
        """
        for buffer in vim.buffers:
            path = Path(buffer.name)
            basename = path.stem
            ext = path.suffix
            if basename.startswith(self.basename) and ext == ".h":
                break
        else:
            logger.debug("Did not find header in buffer list.")
            return None

        # Load the identified buffer first. If it has not already been
        # loaded, it will not have any contents through the api (i.e.
        # len(vim.buffers[n]) will be 0).
        vim.command(f"buffer {buffer.number}")

        # Get the now loaded buffer.
        return vim.buffers[buffer.number]

    def header_fs_search(self, start_levels=1) -> Union[Path, None]:
        """Search filesystem for a potential header to modify.
        """
        root = self.dir.parent
        found = root.glob('**/*.h')
        for candidate in found:
            if candidate.stem == self.basename:
                break
        else:
            logger.error(f"Did not find header file {self.basename}.h")
            return

        prompt = f"Found {candidate}: sync this file? [y/n]: "
        ans = vim.eval(f"input('{prompt}')")

        # Suppress the "Press ENTER or type command to continue" prompt from
        # vim.
        vim.eval('feedkeys("<CR>")')

        if ans.lower() in ["y", "yes"]:
            return candidate
        else:
            return None

    def open_file(self, path) -> None:
        """Opens file into a buffer.
        """
        vim.command(f"edit {path}")
