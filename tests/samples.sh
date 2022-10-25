echo 'Testing samples command...'
python3 featherduster/featherduster.py --debug <<EOF
samples
import manualentry
gdkkn
samples
import clear
samples
exit
EOF
