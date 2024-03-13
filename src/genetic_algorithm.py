import numpy as np
import random
from numpy.random import randint, rand
import pickle
import json
import os
import subprocess
from extract_path import Booksim_log
from init_test import *

class GA_algo:
  def __init__(self, k, n, n_bits, n_chrom, n_iter, r_cross, r_mut, selection_algo):
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
    self.packet_size = 5
    self.selection_algo = selection_algo

    # ==================
    # initialize SD pair table
    # ==================
    # self.ga_table = self.init_table()
    self.ga_table = self.load_from_pickle(f"path_table_n{n}_k{k}.pkl")

    # ==================
    # initialize chromosomes
    # ==================
    self.chromosomes = [self.generate_chrom(self.n_genes, self.n_bits) for _ in range(self.n_chrom)]
    self.sd_pair_mapping = self.generate_sd_pair_mapping()

  def init_table(self):
    ga_init = GA_init(k=self.k, n=self.n, b=self.n_bits, packet_size=self.packet_size)
    ga_init.fill()
    ga_init.display_table()
    ga_init.save_to_pickle(f'path_table_n{n}_k{k}.pkl')

    return ga_init._table

  def load_from_pickle(self, filepath):
    with open(filepath, 'rb') as file:  # Note 'rb' for reading bytes
        return pickle.load(file)

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
      # Move in +y direction
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
      packet_size = {self.packet_size};

      sim_type = latency;

      sample_period  = {cur_time};  

      injection_rate = {inj_rate};

      GA_path_file = decoded_paths.txt; //currently hardcoded, maybe change later
      """
      os.makedirs('config', exist_ok=True)
      # write to config/ga_test_temp
      with open(os.path.join('config', filename), 'w') as config_file:
          config_file.write(config_content.strip())

  def score(self, candidate, traffic):
    # calculate its average latency of this path
    # ================
    paths = self.decode_chromosome_to_paths(candidate)
    decoded_paths = self.decode_chromosome_to_paths(candidate)
    # Save the decoded paths to a txt file
    ga1.save_paths_to_txt(decoded_paths, 'decoded_paths.txt') 
    
    inj_rate = 0.05
    self.generate_config_file(filename="ga_test_temp", traffic=traffic, route_algo="ga", inj_rate=inj_rate)
    with open(f'log/ga_test_temp.log', 'w') as log_file:  
      subprocess.run(["./booksim", "config/ga_test_temp"], stdout=log_file, stderr=log_file)

    LogData = Booksim_log('log/ga_test_temp.log')
    packet_latency = LogData.get_average_latency("Packet")

    return packet_latency

  def mutation(self, chromosome):  
    # choose one random gene -> mutate a bit in its index
    # ================
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
    # crossover 2 parents to create 2 children (new indices)
    # ================
    c1, c2 = p1, p2
    if rand() < self.r_cross:
      pt = randint(self.n_genes)
      c1 = p1[:pt] + p2[pt:]
      c2 = p2[:pt] + p1[pt:]
    return c1, c2
  
  def selection_tournament(self, chromosomes, latencies, k=2):
    selection = []
    for i in (chromosomes):
        selection_ix = randint(0, len(chromosomes)-1)
        rand_selection = [randint(0, len(chromosomes)-1) for _ in range(k)]
        for rand_idx in rand_selection:
            # check if better (e.g. perform a tournament)
            if latencies[rand_idx] < latencies[selection_ix]:
                selection_ix = rand_idx
        selection.append(chromosomes[selection_ix])
    return selection
  
  def selection_roulette(self, chromosomes, latencies, scaling_factor=7.0):
    # Roulette selection: select proportionality based on 
    fitnesses = [1 / latency for latency in latencies]
    total_fitness = sum(fitnesses)
    probabilities = [f / total_fitness for f in fitnesses]
    # Apply scaling factor to probabilities
    scaled_probabilities = [p ** scaling_factor for p in probabilities]
    total_scaled_fitness = sum(scaled_probabilities)
    scaled_probabilities = [p / total_scaled_fitness for p in scaled_probabilities]
    cumulative_probabilities = [sum(scaled_probabilities[:i+1]) for i in range(len(scaled_probabilities))]
    print(f"probabilies scaled: ")
    for p in scaled_probabilities:
       print(f"{p:.3f}")
    selections = []
    for candidate in chromosomes:
        selected_ix = 0
        chance = rand()
        while cumulative_probabilities[selected_ix] <= chance:
            selected_ix += 1
        selections.append(chromosomes[selected_ix])
    # print(f"selections' scores: {[self.score(selection) for selection in selections]}")
    return selections

  def run_GA(self):
    best_chrom_over_history = None
    best_score_over_history = float('inf')
    num_generations_without_improvement = 0
    convergence_threshold = 4
    # prev_best_score = float('inf')
    print("\n-----------------------------------------\n")
    print("Starting running GA iterations")
    for gen in range(self.n_iter):

      # traffic_patterns = ["uniform", "bitcomp", "transpose", "randperm", "shuffle", "diagonal", "asymmetric", "bitrev"]
      # if np.log2(self.N) % 2 != 0:
      #   traffic_patterns.remove("transpose")
      # traffic = random.choice(traffic_patterns)
      traffic = "bitcomp"
      print(f"Trained on traffic={traffic} ")

      scores = [self.score(candidate, traffic) for candidate in self.chromosomes]
      #print(f"\n{gen} iter scores:")
      #print(scores)
      
      best_chrom = None
      best_score = None
      prev_best_score = float('inf')
      # checking exit
      for idx, score in enumerate(scores):
        if best_score is None or score < best_score:
            best_score = score
            best_chrom = self.chromosomes[idx]
        # exit on convergence
        # if prev_best_score is not None:
        #   if best_score >= prev_best_score and gen > n_iter/2:
        #     num_generations_without_improvement += 1
        # else:
        #     num_generations_without_improvement = 0
        prev_best_score = best_score
      print(f"best score is {best_score}")
      print(f"best chrom is {best_chrom}")
      print(f"\n==============================")

      # if num_generations_without_improvement >= convergence_threshold:
      #   print("Convergence reached. Exiting loop.")
      #   break
      
      # select parents
      if selection_algo == 'r':
        selected = self.selection_roulette(self.chromosomes, scores)
      else:
         selected = self.selection_tournament(self.chromosomes, scores)
      scores = [self.score(candidate, traffic) for candidate in selected]
      #print(f"selected scores: \n{scores}")
      print(f"avg score: \n{np.sum(scores)/len(scores)}")

      # create next generation
      new_chromosomes = []
      # crossover and mutation
      for i in range(0, n_chrom, 2):
        # get selected parents in pairs
        p1, p2 = selected[i], selected[i+1]
        c1, c2 = self.crossover(p1, p2)

        for c_idx in range(len(c1)):
          c1[c_idx] = self.mutation(c1[c_idx])
          c2[c_idx] = self.mutation(c2[c_idx])

        new_chromosomes.append(c1)
        new_chromosomes.append(c2)

      self.chromosomes = new_chromosomes
      if best_score < best_score_over_history:
        best_chrom_over_history = best_chrom
        best_score_over_history = best_score
        print(f"new best score!: {best_score_over_history}")
      
      if best_chrom is not None:
        best_paths = self.decode_chromosome_to_paths(best_chrom)
        self.save_paths_to_txt(best_paths, f'ga_paths_n{n}_k{k}_iter{gen}.txt')
      
    return best_score_over_history, best_chrom_over_history

if __name__ == "__main__":
  # define range for input
  k = 2
  n = 3
  n_iter = 10 # num generations
  n_bits = 3
  n_chrom = 2**n_bits  #population size
  r_cross = 0.2 #crossover rate
  r_mut = 2.0 / float(k**n * (k**n - 1)) # average rate of mutation (per chromosome)
  selection_algo = 't' # 'r': roulette or 't': tournament 

  ga1 = GA_algo(k, n, n_bits, n_chrom, n_iter, r_cross, r_mut, selection_algo)

  # example_chromosome = ga1.chromosomes[0]
  # Decode the chromosome to paths using the ga_table
  # decoded_paths = ga1.decode_chromosome_to_paths(example_chromosome)
  # print(decoded_paths)
  # Save the decoded paths to a txt file
  # ga1.save_paths_to_txt(decoded_paths, 'decoded_paths.txt')

  best_score, best_chrom = ga1.run_GA()

  if best_chrom is not None:
    print(f"best all-time score is {best_score}")
    print(f"best all-time chrom is {best_chrom}")
    print(f"\n==============================")
    best_paths = ga1.decode_chromosome_to_paths(best_chrom)
    ga1.save_paths_to_txt(best_paths, f'ga_paths_n{n}_k{k}.txt')
