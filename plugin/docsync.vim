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
