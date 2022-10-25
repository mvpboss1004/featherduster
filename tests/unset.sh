echo 'Testing unset command...'
python3 featherduster/featherduster.py --debug <<EOF
unset
unset foo
use vigenere
set foo=bar
unset foo
exit
EOF
