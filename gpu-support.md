# How to use GPUs in the platform

We will go through the necessery configuration on how to make the KinD cluster utilize available GPUs in local and cloud Ubuntu 22.04 enviroments. We assume that you have not yet created the cluster. The premilinary configuration is the following:

1. Update the enviroment with
```
sudo apt update
sudo apt upgrade # press enter, when you get a list
```
1. [Install Docker](https://docs.docker.com/engine/install/ubuntu/) 
2. [Remove sudo Docker](https://docs.docker.com/engine/install/linux-postinstall/)
3. Check available GPUs
```
lspci | grep -i nvidia
lspci | grep -i amd
lspci | grep -i intel
```

Choose the following configuration based on the available GPUs.

## NVIDIA

### Complete Setup

Assuming your local or cloud enviroment doesn't have NVIDIA drivers, do the following actions:

1. Get driver installers
```
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt install ubuntu-drivers-common
ubuntu-drivers devices
```
2. Install a suitable driver. Some use cases might require upgrading:
```
sudo apt install nvidia-driver-535
```
3. Reboot the enviroment. Be careful in local.
```
Sudo reboot
```
4. Confirm drivers
```
nvidia-smi
```
5. [Install CUDA 12.2](https://forums.developer.nvidia.com/t/installing-cuda-on-ubuntu-22-04-rxt4080-laptop/292899)
6. Confirm CUDA:
```
nvcc --version
```
7. [Configure the container toolkit, docker and kubernetes](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
8. Confirm container toolkit:
```
dpkg -l | grep nvidia-container-toolkit
```
9. Test Docker GPU with
```
docker run --rm -it --gpus=all nvcr.io/nvidia/k8s/cuda-sample:nbody nbody -gpu -benchmark
```
10. [Configure /etc/docker/daemon.json and /etc/nvidia-container-runtime/config.toml](https://www.substratus.ai/blog/kind-with-gpus):
```
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
sudo systemctl restart docker
sudo sed -i '/accept-nvidia-visible-devices-as-volume-mounts/c\accept-nvidia-visible-devices-as-volume-mounts = true' /etc/nvidia-container-runtime/config.toml
```
11. [Change Kind cluster configuration](https://www.substratus.ai/blog/kind-with-gpus): 
```
nodes:
- role: control-plane
  extraMounts:
    - hostPath: /dev/null
      containerPath: /var/run/nvidia-container-devices/all
```
12. Setup OSS with Ray
13. [Add NVIDIA GPU Operator](https://www.substratus.ai/blog/kind-with-gpus)
```
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia || true
helm repo update
helm install --wait --generate-name \
     -n gpu-operator --create-namespace \
     nvidia/gpu-operator --set driver.enabled=false
```
14. [Use the following pod to test GPU Kind](https://github.com/NVIDIA/k8s-device-plugin):
```
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  restartPolicy: Never
  containers:
    - name: cuda-container
      image: nvcr.io/nvidia/k8s/cuda-sample:vectoradd-cuda10.2
      resources:
        limits:
          nvidia.com/gpu: 1
  tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```
15.    Run the pod with
```
kubectl apply -f gpu-test.yaml
```
16.    Configuration works, if the following is showed:
```
$ kubectl logs gpu-pod
[Vector addition of 50000 elements]
Copy input data from the host memory to the CUDA device
CUDA kernel launch with 196 blocks of 256 threads
Copy output data from the CUDA device to the host memory
Test PASSED
Done
```
17. Check the used versions:
```
nvidia-smi
nvcc --version
dpkg -l | grep nvidia-container-toolkit
```
1.  For debugging its recommeded to list working versions. For GPU Ollama in OSS, the working versions were 535.183.01 for drivers, V12.2.91 for CUDA and 1.16.1-1 for container toolkit.

### CUDA Change

If you use case is having wierd problems, it might be caused by old CUDA, which can be updated with the following:

1. Check the current CUDA
```
nvcc --version
```
2. Remove current CUDA:
```
sudo apt-get --purge remove '*cublas*' 'cuda*' 'nsight*' 
sudo apt-get autoremove
```
3. [Install a suitable CUDA version](https://forums.developer.nvidia.com/t/installing-cuda-on-ubuntu-22-04-rxt4080-laptop/292899)
4. Confirm installation with
```
nvcc --version
```

### Driver Change

If you already have NVIDIA drivers in local or cloud enviroment, but they don't for some reason enable your use case, do the following

1. Confirm versions
```
nvidia-smi
nvcc --version
dpkg -l | grep nvidia-container-toolkit
```
2. [Remove NVIDIA driver packages](https://www.jimangel.io/posts/nvidia-rtx-gpu-kubernetes-setup/)
```
sudo apt remove --purge '^nvidia-.*'
sudo apt remove --purge '^libnvidia-.*'
```
3. Clean up
```
sudo apt autoremove
```
4. Restart containerd
```
sudo systemctl restart containerd
```
5. Check the available drivers
```
ubuntu-drivers devices
```
6. Install the suitable driver
```
sudo apt install nvidia-driver-()
```
7. Reboot enviroment
```
sudo reboot
```
8. Check SMI
```
nvidia-smi
```
9. Reinstall by following the previous instructions

---


