import numpy as np
from numpy.random import randint, rand
import pickle
import json
import os
import subprocess
from extract_path import Booksim_log
from init_test import *

class GA_algo:
  def __init__(self, k, n, n_bits, n_chrom, n_iter, r_cross, r_mut):
    # ==================
    # setup param
    # ==================
    self.k = k
    self.n = n
    self.N = k ** n
    self.n_genes = self.N * (self.N - 1)  #k^n * (k^n - 1)  =  # S,D pairs
    self.n_bits = n_bits
    self.n_chrom = n_chrom
    self.n_iter = n_iter
    self.r_cross = r_cross
    self.r_mut = r_mut

    # ==================
    # initialize SD pair table
    # ==================
    self.ga_table = self.init_table()
    # self.ga_table = self.load_from_pickle("path_table_n2_k2.pkl")

    # ==================
    # initialize chromosomes
    # ==================
    self.chromosomes = [self.generate_chrom(self.n_genes, self.n_bits) for _ in range(self.n_chrom)]
    self.sd_pair_mapping = self.generate_sd_pair_mapping()

  def init_table(self):
    ga_init = GA_init(k=self.k, n=self.n, b=self.n_bits)
    ga_init.fill()
    ga_init.display_table()
    # ga_init.save_to_pickle(f'path_table_n{n}_k{k}.pkl')

    return ga_init._table

  # def load_from_pickle(self, filepath):
  #   with open(filepath, 'rb') as file:  # Note 'rb' for reading bytes
  #       return pickle.load(file)

  def generate_chrom(self, n_genes, n_bits):
      # we generate a chromosome as a list of random bitstrings
      return [''.join(str(randint(2)) for _ in range(n_bits)) for _ in range(n_genes)]

  def generate_sd_pair_mapping(self):
      # we create a mapping from gene index to unique SD pair
      sd_pairs = [(src, dest) for src in range(self.N) for dest in range(self.N) if src != dest]
      return sd_pairs

  def decode_chromosome_to_paths(self, chromosome):
      # decode chromosome to paths
      paths = []
      for gene, sd_pair in zip(chromosome, self.sd_pair_mapping):
          gene_index = int(gene, 2)  # Convert binary string to integer
          sd_index = self.convert_SD_to_index(sd_pair[0], sd_pair[1])
          path = self.ga_table[sd_index][gene_index]  # Get the path from ga_table
          paths.append(path)
      return paths

  def convert_SD_to_index(self, src, dst):
      if dst > src:
        index = src * (self.N - 1) + (dst - 1)
      else:
        index = src * (self.N - 1) + dst
      return index

  # def save_paths_to_json(self, paths, filepath):
  #     # Saving paths to JSON file
  #     with open(filepath, 'w') as json_file:
  #         json.dump(paths, json_file, indent=4)
  
  def save_paths_to_txt(self, paths, filepath):
     file = open(filepath, 'w')
     for path in paths:
        file.write(str(path)+"\n")

  def generate_dor_path2d(self): #generate DOR random paths (no deadlock)  list of (x,y) from start to end.
      # a gene is a column in the GA table
      # This gene has {2^(n_bits)-1} possible rows .
      sequence = []
      xi = randint(0, self.k)
      yi = randint(0, self.k)
      xf = xi
      yf = yi
      while (xi, yi) == (xf, yf):
        xf = np.random.choice(0, self.k-1)
        yf = np.random.choice(0, self.k-1)
      x = xi
      y = yi
      sequence.append((x, y))
      # Move in +x direction
      while x < xf:
          x += 1
          sequence.append((x, y))
      # ove in +y direction
      while y < yf:
          y += 1
          sequence.append((x, y))
      while x > xf:
          x -= 1
          sequence.append((x, y))
      while y > yf:
          y -= 1
          sequence.append((x, y))
      return sequence
  
  def generate_config_file(self, filename, route_algo, traffic="uniform", step=1, inj_rate=0.01, cur_time=1000):
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
      packet_size = 5;

      sim_type = latency;

      sample_period  = {cur_time};  

      injection_rate = {inj_rate};

      watch_file = watchlists/watch_ga_1;
      watch_path_out = stats_out/out;
      GA_path_file = decoded_paths.txt; //currently hardcoded, maybe change later
      """
      os.makedirs('config', exist_ok=True)
      # write to config/ga_test_temp
      with open(os.path.join('config', filename), 'w') as config_file:
          config_file.write(config_content.strip())

  def score(self, candidate):
    'calculate its average latency of this path'
    paths = self.decode_chromosome_to_paths(candidate)
    decoded_paths = self.decode_chromosome_to_paths(candidate)
    # Save the decoded paths to a txt file
    ga1.save_paths_to_txt(decoded_paths, 'decoded_paths.txt') 
    self.generate_config_file(filename="ga_test_temp", traffic="uniform", step=1, route_algo="ga", inj_rate=0.1)
    with open(f'log/ga_test_temp.log', 'w') as log_file:  #TODO: .log or .txt
      subprocess.run(["./booksim", "config/ga_test_temp"], stdout=log_file, stderr=log_file)
    subprocess.run(["./booksim", "config/ga_test_temp"])
    LogData = Booksim_log('log/ga_test_temp.log')
    flit_latency = LogData.get_average_latency("Flit")
    print("Flit average latency: ", flit_latency, "\n")
    
    return flit_latency

  def mutation(self, chromosome):  
    'choose one random gene -> mutate a bit in its index'
    if rand() < self.r_mut:
      chromosome_list = list(chromosome)
      # Choose a random index to mutate
      x = randint(len(chromosome_list))
      # Flip the bit
      chromosome_list[x] = str(1 - int(chromosome_list[x]))
      # Convert the list back to a string
      chromosome = ''.join(chromosome_list)
    return chromosome

  def crossover(self, p1, p2):
    '# crossover 2 parents to create 2 children (new indices)'
    c1, c2 = p1, p2
    if rand() < self.r_cross:
      pt = randint(self.n_genes)
      c1 = p1[:pt] + p2[pt:]
      c2 = p2[:pt] + p1[pt:]
    return c1, c2
  
  def selection(self, pop, scores, k=3):
    'tournament selection'
    # first random selection
    selection_ix = randint(len(pop))
    for ix in randint(0, len(pop), k-1):
      # check if better (e.g. perform a tournament)
      if scores[ix] < scores[selection_ix]:
        selection_ix = ix
    return pop[selection_ix]

  def run_GA(self):
    best_chrom = None
    best_score = None
    num_generations_without_improvement = 0
    convergence_threshold = 4
    prev_best_score = float('inf')
    for gen in range(self.n_iter):
      scores = [self.score(candidate) for candidate in self.chromosomes]
      
      # checking exit
      for idx, score in enumerate(scores):
        if best_score is None or score < best_score:
            best_score = score
            best_chrom = self.chromosomes[idx]
      # exit on convergence
      if prev_best_score is not None:
        if best_score >= prev_best_score and gen > n_iter/2:
          num_generations_without_improvement += 1
      else:
          num_generations_without_improvement = 0
      prev_best_score = best_score

      if num_generations_without_improvement >= convergence_threshold:
        print("Convergence reached. Exiting loop.")
        break
      
      # select parents
      selected = [self.selection(self.chromosomes, scores) for _ in range(n_chrom)]
      # create next generation
      children = list()
      # crossover and mutation
      for i in range(0, n_chrom, 2):
        # get selected parents in pairs
        p1, p2 = selected[i], selected[i+1]
        c1, c2 = self.crossover(p1, p2)
        children += c1 + c2
      for c in children:
        self.mutation(c)
      self.chromosomes = children
      
    return best_score, best_chrom

if __name__ == "__main__":
  # define range for input
  k = 2
  n = 2
  n_iter = 1 # num generations
  n_chrom = 8  #population size
  n_bits = 3
  r_cross = 0.5 #crossover rate
  r_mut = 1.0 / float(k**n * (k**n - 1)) # average rate of mutation (per chromosome)

  ga1 = GA_algo(k, n, n_bits, n_chrom, n_iter, r_cross, r_mut)
  # print(ga1.ga_table)

  # print(len(ga1.chromosomes))
  # print(len(ga1.sd_pair_mapping))

  example_chromosome = ga1.chromosomes[0]
  
  # Decode the chromosome to paths using the ga_table
  decoded_paths = ga1.decode_chromosome_to_paths(example_chromosome)
  # print(decoded_paths)

  # Save the decoded paths to a JSON file
  # ga1.save_paths_to_json(decoded_paths, 'decoded_paths.json')
  ga1.save_paths_to_txt(decoded_paths, 'decoded_paths.txt')

  best_score, best_chrom = ga1.run_GA()
