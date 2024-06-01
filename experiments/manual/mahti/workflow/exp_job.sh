#!/bin/bash
#SBATCH --job-name=exp-job
#SBATCH --account=project_()
#SBATCH --partition=medium
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1GB

module load pytorch

echo "Loaded modules:"

module list

echo "Activating venv"

source /users/()/exp_venv/bin/activate

echo "Venv active"

echo "Installed packages"

pip list

echo "Packages listed"

echo "Running training script"

srun python3 exp_train.py ''

echo "Training script complete"