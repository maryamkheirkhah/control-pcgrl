#!/bin/bash 
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=48

## We won't be asking for gpus, for now
##SBATCH --gres=gpu:1

#SBATCH --time=24:00:00
#SBATCH --mem=64GB
#SBATCH --job-name=evopcgrl
#SBATCH --mail-type=BEGIN,END
#SBATCH --mail-user=sam.earle@nyu.edu
#SBATCH --output=evopcgrl_%j.out

cd /scratch/se2161/control-pcgrl

## Is this actually necessary?
source activate

## NOTE THIS ACTUALLY WORKS DONT LISTEN TO THE ERROR MESSAGE ???
conda activate evo-pcgrl

start=$SECONDS
while ! python evolve.py -la 95
do
    duration=$((( SECONDS - start ) / 60))
    echo "Script returned error after $duration minutes"
    if [ $duration -lt 60 ]
    then
      echo "Too soon. Something is wrong. Terminating node."
      exit 42
    else
      echo "Killing ray processes and re-launching script."
      ray stop
      pkill ray
      pkill -9 ray
      pkill python
      pkill -9 python
      start=$SECONDS
    fi
done
