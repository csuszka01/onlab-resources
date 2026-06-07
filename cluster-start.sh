cd /home/csuszka/Documents/egyetem/onlab
echo "starting faas cluster..."

sudo modprobe sch_netem
sudo modprobe nft_compat
sudo modprobe ip_tables
sudo modprobe iptable_filter



k3d cluster start faas-research

echo "Starting port forwards..."
kubectl port-forward -n openfaas svc/gateway 8080:8080 &
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &
kubectl port-forward -n chaos-mesh svc/chaos-dashboard 4000:2333 &

echo "------------------------------------------------"
echo "Environment Ready:"
echo "Grafana:    http://localhost:3000"
echo "Prometheus: http://localhost:9090"
echo "OpenFaaS:   http://localhost:8080"
echo "Chaos mesh: http://localhost:4000"
echo ""
echo "token: "
kubectl -n default create token account-cluster-manager-shito
echo ""
echo "------------------------------------------------"
