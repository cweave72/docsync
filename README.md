# docsync

## Description

docsync is a vim/neovim plugin for synchronizing C function prototypes in a
source file with its header file. In this way, the .c file is the defacto
reference for function docstrings.

It is designed to detect the following C function template:

```c
/******************************************************************************
    [docimport MyLib_someFunction]
*//**
    ...
    <any text>
    ...
******************************************************************************/
myType
MyLib_someFunction(...)
{
...
}
```

It places the following in the header file:
```c
/******************************************************************************
    [docexport MyLib_someFunction]
*//**
    ...
    <any text>
    ...
******************************************************************************/
myType
MyLib_someFunction(...);
```

docsync will first attempt to find the corresponding header in the buffer-list
(matching the name of the source file with a .h extension). If a header is not
found in the buffer-list, it will move up 1 directory level from the path of the
source file and recurse down looking for the matching .h.  If a header file is
found, it will replace all matching function docstrings call signature with the
current source functions.

docsync will not detect:
  * functions defined as static. 
  * functions not matching the above template.

## Installation

Clone this repo and copy the docsync tree into your vim config.

>Note: In the next section, it is assumed you have copied the docsync directory
>to: `$VIMUSERLOCALFILES/custom_plugins/`

## vimrc

Example vimrc snippet:

```vim
source $VIMUSERLOCALFILES/custom_plugins/docsync/plugin/docsync.vim
"Optional control variables.
let g:Docsync_loglevel = "info"         "['critical', 'error', 'info', 'debug']
let g:Docsync_enable_logging = 1              
```

`docsync.vim` 

This is vim's entrypoint into the plugin. You may need to
customize the path in the python heredoc to fit where you copied the files so
that vim can find the python module `docsync.plugin`.

```vim
if !has('python3')
    echomsg ":python3 not available. Docsync will not be loaded."
    finish
endif

python3 << EOF
import sys
import os
import os.path as osp
import vim
plugin_path = os.getenv('VIMUSERLOCALFILES')
plugin_path = osp.join(plugin_path, 'custom_plugins/docsync')
sys.path.insert(0, plugin_path)
EOF

"Default logging level.
let g:Docsync_loglevel = "error"

"Disable logging by default.
let g:Docsync_enable_logging = 0

python3 import docsync.plugin
python3 docsync = docsync.plugin.DocsyncPlugin()

command! Docsync python3 docsync.run()
```

## Customization

To customize to your own function template, modify the regex found in
`docsync.py`:

```python
func_re = re.compile(r"""
    /\*+                                     # Match opening /***************
    \s+\[(?:docimport|docexport)\s+\w*\]\s+  # Match the [docimport funcname] line
    \*//\*\*                                 # Match the token *//**
    .*?                                      # Everything else withing the docstring.
    \*+/\n                                   # Match the closing ************/
    \w+ \s* [*]? \s* (?P<name>\w+) \(.*?\);?  # Match the function signature
""", re.VERBOSE | re.DOTALL)
```
