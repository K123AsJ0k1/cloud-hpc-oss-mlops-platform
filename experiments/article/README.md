# Information Regarding Experiments

## Results

The used time results in the article are found in

- local/artifacts/local_metrics.json (Training time of local-model-training)
- cloud/artifacts/cloud-metrics.json (Training time of cloud-model-training)
- cloud/times/pipeline_data.json (Pipeline time of pipeline)
- cloud-hpc/times/training-1.json (Training time of remote-model-training)
- cloud-hpc/times/components-1.json (Pipeline time of cloud-hpc-pipeline)

Note that local does not use MLOps, which is why it does not have a pipeline time. The reason for the 1 and 2 separation in Cloud-HPC integration is due to its unconfigured and configured states. The difference between them that in unconfigured the integration needs to setup Mahti enviroment such as venvs before submitting the Mahti Ray job. The article uses results of 1 in the table, but in general these results are only slightly different.

The used row results in the article are found in 

- Notebook_Size_Comparison.ipynb (order is local, cloud and cloud-hpc)

The used billing unit results for cloud and cloud-hpc consists of flavor, floating ip and batch job consumption. These are found here

- [CPouta flavors](https://docs.csc.fi/cloud/pouta/vm-flavors-and-billing/): Used flavor is standard.xxlarge with a cost of 8 BU/h
- [Floating IP](https://docs.csc.fi/cloud/pouta/launch-vm-from-web-gui/): Used by all VMs with a cost of 0.2 BU/h
- [Batch jobs](https://docs.csc.fi/computing/performance/): Check cloud-hpc/artifacts/seff-1.json
