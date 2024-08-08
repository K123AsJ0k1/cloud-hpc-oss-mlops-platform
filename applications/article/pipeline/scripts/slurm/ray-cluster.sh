#!/bin/bash
#SBATCH --job-name=ray-cluster
#SBATCH --account=project_()
#SBATCH --partition=medium
#SBATCH --time=00:20:00
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=10GB

module load pytorch

echo "Loaded modules:"

module list

echo "Activating venv"

source /users/()/exp-venv/bin/activate

echo "Venv active"

echo "Installed packages"

pip list

echo "Packages listed"

echo "Setting connection variables"

key_path="/users/()/cpouta-mahti.pem"
cloud_ip="()"
cloud_port=8280
cloud_user="()"
cloud_fip="()"

echo "Setting Ray variables"

hpc_head_port=8265
hpc_dashboard_port=8280 
nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
nodes_array=($nodes)
head_node=${nodes_array[0]}
head_node_ip=$(srun --nodes=1 --ntasks=1 -w "$head_node" hostname --ip-address)

echo "Setting up Ray head"

ip_head=$head_node_ip:$hpc_head_port
export ip_head
echo "IP Head: $ip_head"

echo "Starting HEAD at $head_node"
srun --nodes=1 --ntasks=1 -w "$head_node" \
    singularity_wrapper exec ray start --head --node-ip-address="$head_node_ip" --port=$hpc_head_port --dashboard-host="$head_node_ip" --dashboard-port=$hpc_dashboard_port \
    --num-cpus "${SLURM_CPUS_PER_TASK}" --num-gpus 3 --block &

echo "Setting up SSH tunnel"

ssh -f -o StrictHostKeyChecking=no -i $key_path -N -R $cloud_ip:$cloud_port:$head_node_ip:$hpc_dashboard_port $cloud_user@$cloud_fip

echo "Reverse port forward running"

sleep 5

echo "Setting up Ray workers"

worker_num=$((SLURM_JOB_NUM_NODES - 1))

for ((i = 1; i <= worker_num; i++)); do
    node_i=${nodes_array[$i]}
    echo "Starting WORKER $i at $node_i"
    srun --nodes=1 --ntasks=1 -w "$node_i" \
         singularity_wrapper exec ray start --address "$ip_head" \
	 --num-cpus "${SLURM_CPUS_PER_TASK}" --num-gpus 3 --block &
    sleep 1140
done
