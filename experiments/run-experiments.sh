
COUNT=$(kubectl get podchaos,networkchaos,stresschaos --all-namespaces | wc -l)

if [ "$COUNT" -gt 1 ]; then
    echo "Found $COUNT ChaosExperiments, cleaning up..."
    kubectl delete podchaos,networkchaos,stresschaos --all --all-namespaces
fi

echo "Running all experiments in $PWD"

for file in *.yaml; do
	echo "--> Running $file "
	kubectl apply -f $file
	sleep 122
	echo "    Sleeping 1 min .../n"
	sleep 60
done
echo "--> All experiments done."
