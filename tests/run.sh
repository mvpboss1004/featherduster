echo 'Testing run command...'
python3 featherduster/featherduster.py --debug <<EOF
run
use alpha_shift
run
import manualentry
gdkkn
run
import clear
run
exit
EOF
