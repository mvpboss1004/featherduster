echo 'Testing import clear command...'
python3 featherduster.py --debug <<EOF | grep -v badger
import manualentry
Badger badger badger badger badger badger badger badger badger badger badger
import manualentry
MUSHroom MUSHroom
import clear
samples
exit
EOF
