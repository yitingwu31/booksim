import pickle
import subprocess
import os
from tqdm import tqdm
from extract_path import Flit_path_table

algos_available = ["min_adapt", "xy_yx", "adaptive_xy_yx", "dim_order", "valiant", "planar_adapt", "romm", "romm_ni"]
injec_start_rate = 0.2 #default to 0.3?

class GA_init():
    def __init__(self, k, n, b, rt=algos_available, injection_rates=injec_start_rate):
        self.k = k
        self.n = n
        self.b = b

        self.route_table = rt
        self.injection_rates = injection_rates

        self.total_combs = ((self.k ** self.n) - 1)*(self.k ** self.n)

        # self._table = [[0 for _ in range((k**n-1)*k**n)] for _ in range(2**b)]
        self._table = [{} for _ in range(2**b)]

    def fill(self):
        for i in tqdm(range(2**self.b), desc="Generating Path Table", unit="Rows"):
            cur_inj_rate = self.injection_rates
            cur_time_run = 10000
            traffic_patterns = ["uniform", "bitcomp", "transpose", "randperm", "shuffle", "diagonal", "asymmetric", "bitrev"]
            pattern_to_pick = 0;
            while (len(self._table[i]) != self.total_combs):
                self.generate_config_file(filename="ga_test_temp", route_algo=self.route_table[i], inj_rate=cur_inj_rate, cur_time=cur_time_run, traffic_p=traffic_patterns[pattern_to_pick])
                with open(f'log/temp_log_{i}.txt', 'w') as log_file:
                    subprocess.run(["./booksim", "config/ga_test_temp"], stdout=log_file, stderr=log_file)
                # subprocess.run(["./booksim", "config/ga_test_temp"])
                path_files = f'stats_out/temp_{self.route_table[i]}'
                FlitPathTable = Flit_path_table(n=self.n, k=self.k, filename=path_files)
                uni_paths = FlitPathTable.extract_unique_path()
                for un_path in uni_paths:
                    # We only care about source destination pairs that differ
                    if  un_path[0] != un_path[-1]:
                        # To index  table, we need to generate a unique ID for each SD pair
                        # print(un_path)
                        # print(f"Source: {un_path[0]}, Destination: {un_path[-1]}")
                        sd_pair = (un_path[0], un_path[-1])
                        self._table[i][sd_pair] = un_path
                        # print(f"Configuration {i}, SD pair {sd_pair}: {self._table[i][sd_pair]}")
                if cur_inj_rate < 0.98:
                    cur_inj_rate += 0.02
                cur_time_run += 4000
                pattern_to_pick +=1
                if (pattern_to_pick == len(traffic_patterns)):
                    pattern_to_pick = 0
                # print(f"Found {len(self._table[i])} SD Pairs of {self.total_combs}")

    def display_table(self):
        for row in self._table:
            print(row)
    
    def save_to_pickle(self, filepath):
        with open(filepath, 'wb') as file:  # Note 'wb' for writing bytes
            pickle.dump(self._table, file)
    
    def generate_config_file(self, filename, route_algo, inj_rate=0.01, cur_time=1000, traffic_p = "uniform"):
        config_content = f"""

topology = mesh;
k = {self.k};
n = {self.n};

routing_function = {route_algo};

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

traffic = {traffic_p};
packet_size = 2;

sim_type = latency;

sample_period  = {cur_time};  

injection_rate = {inj_rate};

watch_file = watchlists/watch_ga_1;
watch_path_out = stats_out/temp_{route_algo};
"""
        # Ensure the config directory exists
        os.makedirs('config', exist_ok=True)

        # Write the configuration content to a file in the config directory
        with open(os.path.join('config', filename), 'w') as config_file:
            config_file.write(config_content.strip())


if __name__ == "__main__":
    k = 2 # Nodes per dimension
    n = 2 # Dimension of mesh
    b = 3 # Bits per gene, THis should not be changed - yet. 

    source_dest_pairs = ((k ** n) - 1)*(k ** n)
    # print(f"there are supposed to be {source_dest_pairs} source destination pairs")

    ga_init = GA_init(k,n,b)
    ga_init.fill()
    ga_init.display_table()
    ga_init.save_to_pickle(f'path_table_n{n}_k{k}.pkl')