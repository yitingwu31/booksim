'''
Optimizing the hyperparameters using Optuna
'''
import random, numpy as np, argparse

#############################
import optuna
from genetic_algorithm import GA_algo 

def objective(trial):
    # Fixed values: 
    k = 3
    n = 2
    n_iter = 10
    n_bits = 3
    # Hyperparameters to tune: 
    r_cross = trial.suggest_float('r_cross', 0, 1.0, step=0.1)
    r_mut = trial.suggest_float('r_mut', 0, 1.0, step=0.1)
    n_chrom = trial.suggest_int('n_chrom', 2, 12, step=2)
    string_options = ['r', 't']
    selection_algo = trial.suggest_categorical('selection_algo', string_options)

    # return average best score on 3 iterations of GA: 
    ga1 = GA_algo(k, n, n_bits, n_chrom, n_iter, r_cross, r_mut, selection_algo)
    best_score, best_chrom = ga1.run_GA()
    
    return best_score

def seed_everything(seed=11711):
    random.seed(seed)

if __name__ == "__main__":
    np.random.seed(9999)

    pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=5, interval_steps=1)
    # Create a study object and optimize hyperparameters
    study = optuna.create_study(direction='minimize', pruner=optuna.pruners.MedianPruner(
        n_startup_trials=2, n_warmup_steps=2, interval_steps=1))
    # pruner params: n_startup_trials is # of trials w/o pruning, n_warmup_steps is # of epochs before pruning is allowed, # interval_steps is how frequently to prune
    study.optimize(objective, n_trials=10)


    print("Best trial:")
    trial = study.best_trial
    # Print best hyperparameters and corresponding accuracy
    best_params = study.best_params
    best_accuracy = study.best_value
    print(f"Best Hyperparameters: {best_params}")
    print(f"Best Latency: {best_accuracy}")
    

##########################################################
