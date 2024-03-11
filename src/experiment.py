import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def get_latency(filename, _type):
    latency = float('inf')

    # Extract average information
    lines = [line.rstrip() for line in open(filename, 'r')]
    if "====== Overall Traffic Statistics ======" not in lines:
      print("\nSimulation unstable.")
      return latency
    idx = lines.index("====== Overall Traffic Statistics ======")
    log = lines[idx:]

    # Extract latency of _type packet / network / flit
    if log == []:
      print("\nUnstable simulation has no average latencies.")
      return latency
    
    keyword = _type + " latency average"
    match = [line for line in log if line.startswith(keyword)]
    if len(match) == 0:
        print("\nUnable to find", _type, "average latency.")
        return latency
    
    line = match[0]
    idx1 = line.find('=')
    idx2 = line.find('(')
    latency = float(line[idx1+1:idx2])

    return latency

def generate_config_file(filename, k, n, routing_algo, traffic, inj_rate):
   config_content = f"""

topology = mesh;
k = {k};
n = {n};

routing_function = {routing_algo};

// Flow control
num_vcs     = 8;
vc_buf_size = 8;
wait_for_tail_credit = 1;

// Router architecture
vc_allocator = islip;
sw_allocator = islip;
alloc_iters  = 1;

credit_delay   = 2;
routing_delay  = 0;
vc_alloc_delay = 1;
sw_alloc_delay = 1;

input_speedup     = 2;
output_speedup    = 1;
internal_speedup  = 1.0;

traffic = {traffic};
packet_size = 5;

sim_type = latency;

injection_rate = {inj_rate};
injection_rate_uses_flits=1;

GA_path_file = ga_paths_n{n}_k{k}.txt;
"""
   os.makedirs('config', exist_ok=True)

   with open(os.path.join('config', filename), 'w') as config_file:
      config_file.write(config_content.strip())

def display_results(results, routing_algo, traffic_pattern):
   print("\n========== Results ==========")
   for algo in routing_algo:
      print("\n-----|", algo, "|-----")
      for traffic in traffic_pattern:
         print(traffic, " traffic")
         print(results[algo][traffic])
   print("\n")

def draw_figures(results, routing_algo, traffic_pattern, inj_rate, _type, n, k):
   for traffic in traffic_pattern:
      plt.figure()
      plt.title(f"{traffic} traffic")
      plt.xlabel('Flit injection rate')
      plt.ylabel(f'Average {_type.lower()} latency')
      for algo in routing_algo[::-1]:
         # print(algo)
         good_len = len(results[algo][traffic])
         if float('inf') in results[algo][traffic]:
            good_len = results[algo][traffic].index(float('inf'))
         plt.plot(inj_rate[:good_len], results[algo][traffic][:good_len], label=algo)
      plt.legend(loc='upper left')
      plt.savefig(f'analysis/plots/n{n}k{k}_{_type.lower()}_{traffic}')
      plt.show()

if __name__ == '__main__':
    # routing_algo = ["ga", "min_adapt", "xy_yx", "adaptive_xy_yx", "dim_order", "valiant", "planar_adapt", "romm", "romm_ni"]
   #  traffic_pattern = ["uniform", "bitcomp", "transpose", "randperm", "shuffle", "diagonal", "asymmetric", "bitrev", "bad_dragon", "tornado", "neighbor"]
   #  routing_algo = ["ga", "min_adapt", "adaptive_xy_yx", "valiant"]
    routing_algo = ["ga", "min_adapt"]
    traffic_pattern = ["uniform", "bitcomp", "transpose"]
    inj_rate = [0.01 * i for i in range(1, 7)]
    _type = 'Packet'

    results = {key: {traffic: [] for traffic in traffic_pattern} for key in routing_algo}

    k = 2
    n = 3

    config_file = 'config_test'

    for rate in inj_rate:
       for traffic in traffic_pattern:
          for algo in routing_algo:
            generate_config_file(config_file, k, n, algo, traffic, rate)
            with open(f'log/temp_log.txt', 'w') as log_file:
                print("\n", f"Start running algo: {algo}  traffic: {traffic}  inj_rate: {rate}")
                subprocess.run(["./booksim", f"config/{config_file}"], stdout=log_file, stderr=log_file)
                print("...done!")
            
            latency = get_latency('log/temp_log.txt', _type)
            print("Extracting latencies")
            results[algo][traffic].append(latency)
            print("...done!")

    print("\nInjection rates: ", inj_rate)
    display_results(results, routing_algo, traffic_pattern)
    draw_figures(results, routing_algo, traffic_pattern, inj_rate, _type, n, k)

    df = pd.DataFrame.from_dict(results)
    print(df)
    df.to_csv(f'analysis/n{n}k{k}_{_type.lower()}.csv', index=False)