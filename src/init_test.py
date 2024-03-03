import json
import subprocess
import time
import os

class GA_init():
    def __init__(self, k, n, b, rt, injection_rates):
        self.k = k
        self.n = n
        self.b = b

        self.route_table = rt
        self.injection_rates = injection_rates

        self._table = [[0 for _ in range((k**n-1)*k**n)] for _ in range(2**b)]

    def fill(self):
        start_time = time.time()
        for i in range(2**self.b):
            self.generate_config_file(filename="ga_test_temp", route_algo=self.route_table[i], inj_rate=self.injection_rates)
            subprocess.run(["./booksim", "config/ga_test_temp"])
            # with open('source_dest_pairs.json', 'r') as f:
            #     data = json.load(f)
            #     for j in range((self.k**self.n-1)*self.k**self.n):
            #         self._table[i][j] = data[j]
        end_time = time.time()
        print(f"Time taken to fill: {end_time - start_time} seconds")

    def display_table(self):
        for row in self._table:
            print(row)
    def generate_config_file(self, filename, route_algo, inj_rate=0.01):
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

traffic = uniform;
packet_size = 20;

sim_type = latency;

injection_rate = {inj_rate};

// watch_file = watchlists/watch_ga_1;
watch_path_out = watchlists/temp_{route_algo};
"""
        # Ensure the config directory exists
        os.makedirs('config', exist_ok=True)

        # Write the configuration content to a file in the config directory
        with open(os.path.join('config', filename), 'w') as config_file:
            config_file.write(config_content.strip())


if __name__ == "__main__":
    k = 2 # Nodes per dimension
    n = 2 # Dimension of mesh
    b = 3 # Bits per gene

    injec_rates = 0.1

    algos_available = ["min_adapt", "xy_yx", "adaptive_xy_yx", "dim_order", "valiant", "planar_adapt", "romm", "romm_ni"]

    ga_init = GA_init(k,n,b, algos_available, injection_rates=injec_rates)
    ga_init.fill()
    # ga_init.display_table()