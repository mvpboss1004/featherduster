echo 'Testing search command...'
python3 featherduster/featherduster.py --debug <<EOF
search alpha
search
search thisshouldneverreturnresultsmostlikely
exit
EOF
