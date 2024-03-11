import pickle
import subprocess
import os
import numpy as np
import random
from tqdm import tqdm
from extract_path import *



algos_available = ["min_adapt", "xy_yx", "adaptive_xy_yx", "dim_order", "dim_order_ni", "dim_order_pni", "valiant", "planar_adapt", "romm", "romm_ni", "chaos"]
injec_start_rate = 0.2 #default to 0.3?

class GA_init():
    def __init__(self, k, n, b, rt=algos_available, injection_rates=injec_start_rate, packet_size=5):
        self.k = k
        self.n = n
        self.b = b
        self.N = self.k ** self.n 

        self.route_table = rt
        self.injection_rates = injection_rates

        self.total_combs = ((self.N) - 1)*(self.N)

        # _table should contain at most 2**b paths for each SD pair
        self.num_paths_per_SDpair = 2**b
        # self.num_paths_per_SDpair = 4
        self._table = [None] * (self.N * (self.N-1))
        

        # total N * (N-1) SD pair
        # SD_table contains only one path for each SD pair
        self.SD_table = [None] * (self.N * (self.N-1))

        self.packet_size = packet_size
        self.generate_init_watch_list(filename="watchlists/watch_init")

    def fill(self):
        self.fill_allSDpair()

        # ============================
        # Now len(self._table) = N * (N-1)
        # len(self._table[i]) = 1
        # ============================

        for i in tqdm(range(len(algos_available)), desc="Generating Path Table", unit="Rows"):
            # cur_inj_rate = self.injection_rates
            cur_time_run = 10000
            traffic_patterns = ["uniform", "bitcomp", "transpose", "randperm", "shuffle", "diagonal", "asymmetric", "bitrev", "bad_dragon", "tornado", "neighbor"]
            if np.log2(self.N) % 2 != 0:
                traffic_patterns.remove("transpose")
            
            route_algo = self.route_table[i]
            for traffic in traffic_patterns:
                
                inj_rate_list = [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3]

                for cur_inj_rate in inj_rate_list:
                    # ============================
                    # run booksim simulation
                    # ============================
                    
                    print(f"............. run booksim with route_algo={route_algo}, traffic={traffic} .............")
                    
                    self.generate_watch_list('watchlists/watch_temp')
                    self.generate_config_file(filename="ga_test_temp", watch_file='watchlists/watch_temp',
                                            watch_path_out="watchlists/temp_watch_out",
                                            route_algo=route_algo, inj_rate=cur_inj_rate, 
                                            cur_time=cur_time_run, traffic=traffic, 
                                            packet_size=self.packet_size)
                    with open(f'log/temp_log.txt', 'w') as log_file:
                        subprocess.run(["./booksim", "config/ga_test_temp"], stdout=log_file, stderr=log_file)
                    
                    # ============================
                    # extract unique path from simulation watch_path_out
                    # ============================
                    FlitPathTable = Flit_path_table(n=self.n, k=self.k, filename="watchlists/temp_watch_out")
                    uni_paths = FlitPathTable.extract_unique_path()
                    print(f"unipath = {len(uni_paths)}")
                    # ============================
                    # fill in _table with uniPath
                    # ============================
                    self.fill_table_with_uniPath(uni_paths)

                    # print("new table size for each SD pair")
                    for tt in range(len(self._table)):
                        print(len(self._table[tt]), end="   ")
                    print("\n")
                    
                    # ============================
                    # update config combination
                    # ============================
                    # if cur_inj_rate < 0.98:
                    #     cur_inj_rate += 0.02
                    # cur_time_run += 4000

        self.fill_table_row()

    def fill_allSDpair(self):
        traffic = "custom_neighbor"
        route_algo = "dor"
        inj_rate = 0.1
        for i in range(1, self.N):
            # ============================
            # customized traffic sending (S, D) = (n, n + step)
            # iterate step from 1 to N-1, filling all SD pair
            # ============================
            step = i
            self.generate_config_file(filename="ga_test_temp", watch_file="watchlists/watch_init",
                                    watch_path_out="watchlists/temp_watch_init_out",
                                    traffic=traffic, step=step, route_algo=route_algo, inj_rate=inj_rate)
            subprocess.run(["./booksim", "config/ga_test_temp"])
            if i == 1:
                self.generate_watch_list(filename='watchlists/watch_init')
                subprocess.run(["./booksim", "config/ga_test_temp"])

            # ============================
            # extract unipath from simulation watch_path_out
            # ============================
            FlitPathTable = Flit_path_table(n=self.n, k=self.k, filename="watchlists/temp_watch_init_out")
            uni_paths = FlitPathTable.extract_unique_path()
            
            # ============================
            # fill in SD table with uniPath
            # ============================
            self.fillSDtable_with_uniPath(uni_paths)

        self.display_SDtable()

        # ============================
        # initialize _table with SD_table
        # ============================
        self._table = [[path] for path in self.SD_table]

    def fillSDtable_with_uniPath(self, uni_paths):
        for path in uni_paths:
            # ignore self sending ones
            if len(path) < 2:
                continue

            # ============================
            # calculate SD table index from src, dest
            # ============================
            # type(path) = tuple
            src = path[0]
            dest = path[-1]

            # convert to SD table index 
            if dest > src:
                index = src * (self.N - 1) + (dest - 1)
            else:
                index = src * (self.N - 1) + dest

            # ============================
            # fill in SD table
            # ============================
            self.SD_table[index] = path


    def fill_table_with_uniPath(self, uni_paths):
        for path in uni_paths:
            # ignore self sending ones
            if len(path) < 2:
                continue

            # ============================
            # calculate SD table index from src, dest
            # ============================
            # type(path) = tuple
            src = path[0]
            dest = path[-1]
            if src == dest:
                continue

            # convert to SD table index 
            if dest > src:
                sd_index = src * (self.N - 1) + (dest - 1)
            else:
                sd_index = src * (self.N - 1) + dest
            
            # ============================
            # fill in table if path sequence doesn't exist before (only store unique path)
            # ============================
            if path not in self._table[sd_index]:
                self._table[sd_index].append(path)
                
    def fill_table_row(self):
        for i in range(len(self._table)):
            tb_len = len(self._table[i])
            # if not enough unique path, just fill up the rows with existing ones
            if tb_len < self.num_paths_per_SDpair:
                print("Initial table row ", tb_len, " filling to 8 rows...\n")
                for k in range(self.num_paths_per_SDpair - tb_len):
                    idx = np.random.randint(tb_len)
                    self._table[i].append(self._table[i][idx])

            elif tb_len > self.num_paths_per_SDpair:
                path_len = np.array([len(path) for path in self._table[i]])
                minimal_idx = np.argmin(path_len)
                sample_table = random.sample(self._table[i], self.num_paths_per_SDpair)
                # make sure minimal path is always included
                if self._table[i][minimal_idx] not in sample_table:
                    sample_table[0] = self._table[i][minimal_idx]
                self._table[i] = sample_table
                


    def display_SDtable(self):
        # ============================
        # check num of unfilled SDpair
        # ============================
        print("\n========================\n")
        num_unfilled_SDpair = self.SD_table.count(None)
        if num_unfilled_SDpair == 0:
            print("all SD pair are filled!")
        else:
            print(f"Already have {len(self.SD_table) - num_unfilled_SDpair} pairs.")
            print(f"Still {num_unfilled_SDpair} SD pair unfilled.")
        
        print(self.SD_table)
        print("\n========================\n")


    def display_table(self):
        print("\n========================\n")
        print(" (S, D) \t\t num of paths \t\tpaths")
        print("-------------------------------------------------------------------------")
        for src in range(self.N):
            for dest in range(self.N):
                if src == dest:
                    continue
                
                if dest > src:
                    sd_index = src * (self.N - 1) + (dest - 1)
                else:
                    sd_index = src * (self.N - 1) + dest

                print(f"({src}, {dest}) \t\t\t {len(self._table[sd_index])} \t\t\t {self._table[sd_index]}")
        print("\n========================\n")

    def save_to_pickle(self, filepath):
        with open(filepath, 'wb') as file:  # Note 'wb' for writing bytes
            pickle.dump(self._table, file)
    
    def generate_watch_list(self, filename):
        traffic = "custom_neighbor"
        route_algo = "dor"
        stats_out = Booksim_stats_out(f"stats_out/temp_{traffic}_{route_algo}")
        fid_list = stats_out.fid
        with open(filename, 'w') as f:
            for fid in fid_list:
                f.write(f"{fid}\n")

    def generate_init_watch_list(self, filename):
        with open(filename, 'w') as f:
            for i in range(self.N):
                f.write(f"{i * self.packet_size}\n")
    
    def generate_config_file(self, filename, watch_file, watch_path_out, route_algo, traffic="uniform", step=1, inj_rate=0.01, cur_time=1000, packet_size=1):
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

traffic = {traffic};
neighbor_step = {step};
packet_size = {packet_size};

sim_type = latency;

// sample_period  = {cur_time};  

injection_rate = {inj_rate};

watch_file = {watch_file};
watch_path_out = {watch_path_out};
stats_out = stats_out/temp_{traffic}_{route_algo};
"""
        # Ensure the config directory exists
        os.makedirs('config', exist_ok=True)

        # Write the configuration content to a file in the config directory
        with open(os.path.join('config', filename), 'w') as config_file:
            config_file.write(config_content.strip())


if __name__ == "__main__":
    k = 2 # Nodes per dimension
    n = 3 # Dimension of mesh
    b = 3 # Bits per gene, THis should not be changed - yet. 

    # source_dest_pairs = ((k ** n) - 1)*(k ** n)
    # print(f"there are supposed to be {source_dest_pairs} source destination pairs")

    ga_init = GA_init(k, n, b)
    ga_init.fill()
    ga_init.display_table()
    # ga_init.save_to_pickle(f'path_table_n{n}_k{k}.pkl')
