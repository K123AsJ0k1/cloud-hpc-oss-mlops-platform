# Information Regarding Experiments

## Note on Results

The used time results in the article are found in

- local/artifacts/local_metrics.json
- cloud/artifacts/cloud-metrics.json
- cloud/times/pipeline_data.json
- cloud-hpc/times/components-1.json
- cloud-hpc/times/training-1.json

The reason for the 1 and 2 separation in Cloud-HPC integration is due to its unconfigured and configured states. The difference between them that in unconfigured the integration needs to setup Mahti enviroment such as venvs before submitting the Mahti Ray job. The article uses results of 1 in the table, but in general these results are only slightly different.

The used row results in the article are found in 

- Notebook_Size_Comparison.ipynb

The used billing unit results for cloud and cloud-hpc consists of flavor, floating ip and batch job consumption. These are found here

- [CPouta flavors](https://docs.csc.fi/cloud/pouta/vm-flavors-and-billing/): Used flavor is standard.xxlarge
- [Floating IP](https://docs.csc.fi/cloud/pouta/launch-vm-from-web-gui/): Used by all VMs
- [Batch jobs](https://docs.csc.fi/computing/performance/): Check seff-1.json
