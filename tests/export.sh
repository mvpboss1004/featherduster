echo 'Testing FeatherDuster export command...'
python3 featherduster/featherduster.py --debug << EOF 
import manualentry
gdkkn
use alpha_shift
run
export
/tmp/fd_output
EOF
grep hello /tmp/fd_output
