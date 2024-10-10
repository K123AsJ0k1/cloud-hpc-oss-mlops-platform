# Setup Integreated OSS Platform

### OSS Modifications

1. In kubeflow/in-cluster-setup/kubeflow/kustomization.yaml the following components are removed
   - Katib, 
   - Jupyter web app
   - Notebook controlelr
   - PVC viewere
   - Volumes web app
   - Tensorboards controller
   - Tensorboard web app
   - Training operator
2. MinIO image in minio-deployment.yaml was changed to newest
3. A new MLflow image was created and set in mlflow-deployment.yaml
4. PostgreSQL image in postgresql-deployment.yaml was changed to newest
5. In monitoring/kustomization.yaml the following components are removed
   - Alert manager 
   - Pushgateway
6. Prometheus image in prometheus-deployment.yaml was changed to newest
7. Grafana image in grafana-deployment.yaml was changed to newest
8. Forwarder deployment was added
9. The deployment envs were modified to have the forwarder deployment

### CPouta OSS

#### Basics

In order to use CSC services, you need to create an CSC account, so please check the following official documentation:

- [Creation of CSC user account](https://docs.csc.fi/accounts/how-to-create-new-user-account/)
- [Getting service access](https://docs.csc.fi/accounts/how-to-add-service-access-for-project/) 
- [Cloud computing concepts](https://docs.csc.fi/cloud/)
- [Pouta security guidelines](https://docs.csc.fi/cloud/pouta/security/)
- [Pouta accounting](https://docs.csc.fi/cloud/pouta/accounting/)

#### Context

If you want to understand the technical details, check these links:

Mahti:
- [What is Mahti]( https://docs.csc.fi/support/tutorials/mahti_quick/)
- [Mahti partitions](https://docs.csc.fi/computing/running/batch-job-partitions/)
- [Connection to Mahti](https://docs.csc.fi/computing/connecting/)
- [Creating batch scripts for Mahti](https://docs.csc.fi/computing/running/creating-job-scripts-mahti/)
- [Example batch job scripts for Mahti](https://docs.csc.fi/computing/running/example-job-scripts-mahti/)
- [Python on CSC supercomputers](https://docs.csc.fi/apps/python/#installing-python-packages-to-existing-modules)

SSH:
- [Adding a new SSH key into cloud servers](https://www.servers.com/support/knowledge/linux-administration/how-to-add-new-ssh-key-to-a-cloud-server)
- [SSH connection "not possible"](https://askubuntu.com/questions/1399009/ssh-connection-not-possible-host-key-verification-failed)
- [SSH private key is too open](https://stackoverflow.com/questions/9270734/ssh-permissions-are-too-open)
- [How to create SSH tunnels](https://www.ssh.com/academy/ssh/tunneling-example)
- [Remote binding to localhost](https://serverfault.com/questions/997124/ssh-r-binds-to-127-0-0-1-only-on-remote)

Ray:
- [Running ray on SLURM](https://docs.ray.io/en/latest/cluster/vms/user-guides/community/slurm.html)

Headless services:
- [External services in kubernetes](https://stackoverflow.com/questions/57764237/kubernetes-ingress-to-external-service?noredirect=1&lq=1)
- [Headless services in kubernetes](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)

#### OSS Setup

When you have managed to get a CSC user with a project with a access to [CPouta](https://pouta.csc.fi), you are now able to create virtual machine instances for running OSS. Please check the following offical documentation:

- [VM Creation](https://docs.csc.fi/cloud/pouta/launch-vm-from-web-gui/)
- [VM Flavors](https://docs.csc.fi/cloud/pouta/vm-flavors-and-billing/#standard-flavors)
- [VM connection](https://docs.csc.fi/cloud/pouta/connecting-to-vm/)

Use the documentation to setup a VM instance with the following details:

- Instance name: OSS-Platform (Can be changed)
- Flavor: Standard.xxlarge
- Instance Count: 1
- Instance Boot Source: Boot from image
- Image Name: Ubuntu-22.04

and a local SSH config with the following:

```
Host cpouta
Hostname ()
User ()
IdentityFile ~/.ssh/local-cpouta.pem
```

When you have connected to the VM instance, run the following commands

```
sudo apt update
sudo apt upgrade # press enter, when you get a list
```

We now need to install and configure Docker, so please use the following official documentation:

- [Docker engine setup](https://docs.docker.com/engine/install/ubuntu/)
- [Remove sudo docker](https://docs.docker.com/engine/install/linux-postinstall/)

We can provide more storage for Docker with the following actions:

1. [Create and mount atleast 500GB volume into a VM](https://docs.csc.fi/cloud/pouta/persistent-volumes/)
2. Check current root directory:
```
docker info
```
3. Create a folder in volume
```
cd /media/volume
mkdir docker
```
4. Get its path
```
cd docker
pwd
```
5. Check the docker daemon.json
```
cat /etc/docker/daemon.json
```
6. Shutdown docker
```
sudo systemctl stop docker
sudo systemctl stop docker.socket
sudo systemctl stop containerd
```
7. Edit to have data-root: '/media/volume/docker':
```
sudo nano /etc/docker/daemon.json
```
8. Confirm path:
```
cat /etc/docker/daemon.json
```
9.  Move docker data: 
```
sudo rsync -axPS /var/lib/docker/ /media/volume/docker
```
10. Restart docker
```
sudo systemctl start docker
```
11. Check docker info
```
docker info
```
12. Try running a container
13. If no failures happen, check file system utilization with
```
df -h
```

The VM is now ready to setup OSS, so git clone this repository and install any deployment with monitoring. When OSS is running, you can use the following tools:

```
# Kubeflow central dashboard
ssh -L 8080:localhost:8080 cpouta
kubectl port-forward svc/istio-ingressgateway 8080:80 -n istio-system
http://localhost:8080

# Kubeflow MinIO
ssh -L 9000:localhost:9000 cpouta
kubectl port-forward svc/minio-service 9000:9000 -n kubeflow
http://localhost:9000 (user is minio and password minio123)

# MLflow
ssh -L 5000:localhost:5000 cpouta
kubectl port-forward svc/mlflow 5000:5000 -n mlflow 
http://localhost:5000

# MLflow MinIO
ssh -L 9001:localhost:9001 cpouta
kubectl port-forward svc/mlflow-minio-service 9001:9001 -n mlflow
http://localhost:9001 (user and password is minioadmin)

# Prometheus
ssh -L 8090:localhost:8090 cpouta
kubectl port-forward svc/prometheus-service 8090:8080 -n monitoring
http://localhost:8090

# Grafana
ssh -L 5050:localhost:5050 cpouta
kubectl port-forward svc/grafana 5050:3000 -n monitoring
http://localhost:5050 (user and password is admin)

# Forwarder frontend

ssh -L 6500:localhost:6500 cpouta
kubectl port-forward svc/fastapi-service 6500:6500 -n forwarder

# Forwarder Monitor

ssh -L 6501:localhost:6501 cpouta
kubectl port-forward svc/flower-service 6501:6501 -n forwarder

# Forwarder Backend

ssh -L 6502:localhost:6502 cpouta
kubectl port-forward svc/celery-service 6502:6502 -n forwarder

# Ray Dashboard

ssh -L 127.0.0.1:8280:192.168.1.13:8280 cpouta
```

### Ray Setup

When you have access to Allas and Mahti, in order to use Mahti Ray in CPouta, we need to configure security groups and SSH. Set the VM security group to have the following:

- Mahti-nat-1.csc.fi
   - SSH
   - 86.50.165.201
- Mahti-nat-2.csc.fi
   - SSH
   - 86.50.165.202
  
For the VM SSH configuration, change GatewayPorts to be clientspecified with:

```
cat /etc/ssh/sshd_config
sudo nano /etc/ssh/sshd_config 
CTRL + X 
Enter 
sudo service ssh restart 
```

You can debug SSH connections with:

```
grep sshd /var/log/auth.log # CPouta
```


### Notebook Setup

In order to get the Allas token used in storage interactions, you need to create a .env in SSH folder with the following:

```
CSC_USERNAME = ""
CSC_PASSWORD = ""
CSC_USER_DOMAIN_NAME = "Default"
CSC_PROJECT_NAME = "project_()"
```

### Submitter Setup


In order to integrate CPouta OSS and Mahti Ray, you need to use a locally run submitter to handle SSH based SLURM interactions. In order to make the submitter run with compose, do the following:


1. Go to .ssh folder and use the following template to create compose-secrets.json:
```
{
    "CLOUD_ENVIROMENT": "none",
    "CLOUD_ADDRESS": "none",
    "CLOUD_USER": "none",
    "CLOUD_KEY": "none",
    "CLOUD_PASSWORD": "empty", # password or empty
    "STORAGE_ENVIROMENT": "allas",
    "STORAGE_USER": "token", # Allas is always token based
    "STORAGE_PASSWORD": "token", # Allas is always token based
    "HPC_ENVIROMENT": "mahti",
    "HPC_ADDRESS": "mahti.csc.fi",
    "HPC_USER": "", # CSC user
    "HPC_KEY": "/run/secrets/local-mahti",
    "HPC_PASSWORD": "empty", # password or empty
    "INTEGRATION_ENVIROMENT": "cpouta-mahti",
    "INTEGRATION_KEY": "/run/secrets/cpouta-mahti",
    "INTEGRATION_PASSWORD": "empty" # password or empty
}

```
1. Use SSH key section of this [guide](https://docs.csc.fi/cloud/pouta/launch-vm-from-web-gui/#setting-up-ssh-keys) to create cpouta-mahti.pem files and save it into .ssh. Its recommeded that bridge key doesn't get passphrase.
2. Use SSH key section of this [guide](https://docs.csc.fi/computing/connecting/) to create local-mahti.pem file and save it to .ssh
3. Setup up the following .ssh/config:
```
Host mahti
Hostname mahti.csc.fi
User ()
IdentityFile ~/.ssh/local-mahti.pem
```
4. Test that SSH works:
   
```
ssh mahti
exit/logout # CTRL + C if hangs
```
5. Get the absolute paths of the compose-secrets.json and keys with 'pwd' and write them into the compose-secrets.json alongside the passphrases of CPouta and Mahti SSH keys
6. Go to the production deployemnt folder of submitter in applications and make the submitter run locally with:

```
docker compose -f stack.yaml up # Start
CTRL + C # Shutdown
docker compose -f stack.yaml down # Shutdown
```
7. If now errors are created, proceed to the local, cloud and cloud-hpc notebooks

## Troubleshooting

**Error: response from daemon: driver failed programming external connectivity on endpoint kind-ep-control-plane**

This error is related to a existing docker [issue](https://github.com/moby/moby/issues/25981), where docker-proxy binds to ports when no containers run or exist. There isn't permanent solution, but the temporary solution is the following:

```
netstat -tuln # Check active ports
sudo systemctl stop docker
sudo rm -rf /var/lib/docker/network/files
sudo systemctl start docker
netstat -tuln # Check that the port is gone
```

Sometimes this doesn't work, but fortunelly in those cases we can do the following:

```
sudo lsof -i :port
sudo kill (shown PID)
```

**Error: could not kill running container when trying to delete kind registry**

Sometimes when you try to remove kind registry, you receive permission denied error. There isn't a permanent solution, but we can temporarily fix it with the following command:

```
docker ps 
sudo ps awx | grep containerd-shim | grep <<container_id>> | awk '{print $1}'
sudo kill -9 <<process_id>>
```
