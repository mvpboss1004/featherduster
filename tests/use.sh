echo 'Testing use command...'
python3 featherduster/featherduster.py --debug <<EOF
use thisisnotarealmodule
use alpha_shift
exit
EOF
