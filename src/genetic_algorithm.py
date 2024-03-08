from numpy.random import randint
from numpy.random import rand

import numpy as np
import random
from init_test import GA_init
import pickle
import json


class GA_algo:
  def __init__(self, k, n, n_bits, n_chrom, n_iter, r_cross, r_mut):
     self.k = k
     self.n = n
     self.N = k ** n
     self.n_genes = k**n * (k**n - 1)  #k^n * (k^n - 1)  =  # S,D pairs
     self.n_bits = n_bits
     self.n_chrom = n_chrom
     self.n_iter = n_iter
     self.r_cross = r_cross
     self.r_mut = r_mut
    #  self.ga_table = GA_init(k, n, n_bits).fill()._table #TODO later: expand to all rt, injection rates
     self.ga_table = self.load_from_pickle("path_table.pkl")

     self.chromosomes = [self.generate_chrom(self.n_genes, self.n_bits) for _ in range(self.n_chrom)]
     self.sd_pair_mapping = self.generate_sd_pair_mapping()


  def load_from_pickle(self, filepath):
    with open(filepath, 'rb') as file:  # Note 'rb' for reading bytes
        return pickle.load(file)

  def generate_chrom(self, n_genes, n_bits):
      # Generate a chromosome as a list of random bitstrings
      return [''.join(str(randint(2)) for _ in range(n_bits)) for _ in range(n_genes)]

  def generate_sd_pair_mapping(self):
      # Create a mapping from gene index to unique SD pair
      sd_pairs = [(src, dest) for src in range(self.k**self.n) for dest in range(self.k**self.n) if src != dest]
      return sd_pairs

  def decode_chromosome_to_paths(self, chromosome):
      # Decoding chromosome to paths
      paths = []
      for gene, sd_pair in zip(chromosome, self.sd_pair_mapping):
          gene_index = int(gene, 2)  # Convert binary string to integer
          path = self.ga_table[gene_index][sd_pair]  # Get the path from ga_table
          paths.append(path)
      return paths
  
  def convert_SD_to_index(self, src, dst):
     if dst > src:
        index = src * (self.N - 1) + (dst - 1)
     else:
        index = src * (self.N - 1) + dst

  def save_paths_to_json(self, paths, filepath):
      # Saving paths to JSON file
      with open(filepath, 'w') as json_file:
          json.dump(paths, json_file, indent=4)
  
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
  
  def score(self, candidate):
    'calculate its average latency of this path.  (based on latency == shorter latency means higher score)'
    # TODO: replace. call booksim simulation at low % and read this datapath's real latency! 
    # 1. decode candidate "111" "001" into real paths. Write into routefunction? 
    paths = self.decode(candidate)
    sum_score = 0
    # TODO: Evaluate chromosome (run in booksim)
    for path in paths:
        # TODO: run booksim(path)
        sum_score += path
    
    return sum_score

  def mutation(self):  
    'choose one random gene -> mutate a bit in its index'
    for i in range(len(self.bitstring)):
      # check for a mutation
      if rand() < self.r_mut:
        # flip the bit
        self.bitstring[i] = 1 - self.bitstring[i]

  def crossover(self, p1, p2):
    '# crossover 2 parents to create 2 children (new indices)'
    c1, c2 = p1.copy(), p2.copy()
    if rand() < self.r_cross:
      pt = randint(1, len(p1)-2)
      c1 = p1[:pt] + p2[pt:]
      c2 = p2[:pt] + p1[pt:]
    return [c1, c2]
  
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
    population = [self.generate_chrom(self.n_genes, n_bits) for chrom in range(n_chrom)]
    best_chrom, best_score = None
    for gen in range(n_iter): #TODO: or exit if delta converges
      scores = [self.score(candidate) for candidate in population]
      # select parents
      selected = [self.selection(population, scores) for _ in range(n_chrom)]
      # create next generation
      children = list()
      # crossover and mutation
      for i in range(0, n_chrom, 2):
        # get selected parents in pairs
        p1, p2 = selected[i], selected[i+1]
        for c in self.crossover(p1, p2, r_cross):
          self.mutation(c, r_mut)
          children.append(c)
      population = children
      # determine best:
      new_scores = [self.score(candidate) for candidate in population]
      for c in new_scores:
        if new_scores > best_score:  #TODO: decide score > or <
            best_score = new_scores
            best_chrom = c
    return best_score, best_chrom
  
  def generate_chrom(self, n_genes, n_bits):
    'init a random chromosome for testing               in real C++ = (run GAinit.py )'
    bitstrings_array = np.random.randint(2, size=(n_genes, n_bits))  # random gene bits
    chromosome = [''.join(str(bit) for bit in bits) for bits in bitstrings_array] #join as one string
    return chromosome

if __name__ == "__main__":
  # define range for input
  k = 2
  n = 2
  n_iter = 6 # num generations
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
  ga1.save_paths_to_json(decoded_paths, 'decoded_paths.json')
  ga1.save_paths_to_txt(decoded_paths, 'decoded_paths.txt')


  #TODO: convert this best chrom chart into a set of routes
  # deterministic_path = GA_algo.decode(best_chrom)
  #TODO: run booksim on this "best" route