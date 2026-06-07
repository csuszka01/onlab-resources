
echo "Figlet test: 100 request/second."
while true; do
	echo "Ez egy tudomanyos kiserlet. Lathatnam az engedelyet? Hat persze..." | faas-cli invoke figlet > /dev/null;
	sleep 0.005
done
