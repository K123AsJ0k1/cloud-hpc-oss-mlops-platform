from prometheus_client import Gauge

# Created and works
def seff_gauge(
    prometheus_registry: any    
) -> any:
    gauge = Gauge(
        name = 'cloud_hpc_bridge_job_seff_metrics',
        documentation = 'SLURM Seff metrics collected from completed jobs',
        labelnames = [
            'sampleid',
            'user',
            'jobid',
            'jobname',
            'project',
            'cluster', 
            'state',
            'metric'
        ],
        registry = prometheus_registry
    )
    
    names = {
        'nodes': 'Nod',
        'cores-per-node': 'CoPeNod',
        'cpu-utilized-seconds': 'CPUUSec',
        'cpu-efficiency-percentage': 'CPUEffPe',
        'cpu-efficiency-seconds': 'CPUEffSec',
        'job-wall-clock-time-seconds': 'JoWaClTISec',
        'memory-utilized-bytes': 'MemUtiByte',
        'memory-efficiency-percentage': 'MemEffPe',
        'memory-efficiency-bytes': 'MemEffByte',
        'billing-units': 'BiUn'
    }
    return gauge, names
# Created and works
def sacct_gauge(
    prometheus_registry: any 
) -> any:
    gauge = Gauge(
        name = 'cloud_hpc_bridge_job_sacct_metrics',
        documentation = 'SLURM Sacct metrics collected from completed jobs',
        labelnames = [
            'sampleid',
            'row',
            'user',
            'jobid',
            'jobname',
            'partition',
            'state',
            'metric'
        ],
        registry = prometheus_registry
    )
    # Add Byte into RSS and VM
    names = {
        'req-cpus': 'RqCPUS',
        'alloc-cpus': 'AcCPUS',
        'req-nodes': 'RqNod',
        'alloc-nodes': 'AcNod',
        'ave-cpu-seconds': 'AvCPUSec',
        'ave-cpu-freq-khz': 'AvCPUFreqkhz',
        'ave-disk-read-bytes': 'AvDiReByte',
        'ave-disk-write-bytes': 'AvDiWrByte',
        'ave-pages': 'AvPas',
        'ave-rss-bytes': 'AvRSS',
        'ave-vm-size-bytes': 'AvVMSi',
        'consumed-energy-raw-joule': 'CodEnyJoule',
        'timelimit-seconds': 'TiLiSec',
        'elapsed-seconds': 'ElaSec',
        'planned-seconds': 'PlaSec',
        'planned-cpu-seconds': 'PlaCPUSec',
        'cpu-time-seconds': 'CPUTiSec',
        'total-cpu-seconds': 'ToCPUSec',
        'submit-time': 'SuTi',
        'start-time': 'StTi',
        'end-time': 'EnTi'
    }
    return gauge, names
# Created and works
def time_gauge(
    prometheus_registry: any 
) -> any:
    gauge = Gauge(
        name = 'cloud_hpc_bridge_job_time_metrics',
        documentation = 'Time metrics collected from porter and submitter actions',
        labelnames = [
            'sampleid',
            'collector',
            'area',
            'action',
            'metric'
        ],
        registry = prometheus_registry
    )
    names = {
        'total-seconds': 'ToSec'
    }
    return gauge, names