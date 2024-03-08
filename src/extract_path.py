'''
Helper code to extract unique flit path from watch_out
'''
class Flit_path_table:
  def __init__(self, n, k, filename):
    self.n = n
    self.k = k
    self.flit_path_map = {}
    self.extract_flit_path(filename)

  def extract_flit_path(self, filename):
    f = open(filename, "r")
    lines = f.readlines()
    for line in lines:
      flit_name = line.split(" | ")[0]
      flit_id = flit_name.split()[1]
      packet_id = flit_name.split()[3][:-1]

      if flit_id not in self.flit_path_map.keys():
        self.flit_path_map[flit_id] = []

      if "src" in line:
        src = int(line.split()[-1][:-1])
      elif "dest" in line:
        dest = int(line.split()[-1][:-1])
      else:
        mid_fullname = line.split()[-1][:-1].split("/")[-1]
        if self.n == 2:
          yid = int(mid_fullname.split("_")[1])
          xid = int(mid_fullname.split("_")[2])
          mid = yid * self.k + xid
        if self.n == 3:
          zid = int(mid_fullname.split("_")[1])
          yid = int(mid_fullname.split("_")[2])
          xid = int(mid_fullname.split("_")[3])
          mid = zid * self.k * self.k + yid * self.k + xid
        self.flit_path_map[flit_id].append(mid)

  def extract_unique_path(self):
    paths = self.flit_path_map.values()
    unipaths = set(tuple(i) for i in paths)
    return unipaths


'''
Helper code to extract flit latency and check saturation
'''
class Booksim_log:
  def __init__(self, filename): 
    self.filename = filename
    self.log = self.extract_log(filename)
  
  def extract_log(self, filename):
    lines = [line.rstrip() for line in open(filename, 'r')]
    if "====== Overall Traffic Statistics ======" not in lines:
      print("\nSimulation unstable.")
      return []
    idx = lines.index("====== Overall Traffic Statistics ======")
    return lines[idx:]
  
  def get_average_latency(self, type):
    if self.log == []:
      print("\nUnstable simulation has no average latencies.")
      return float('inf')
    
    keyword = type + " latency average"
    match = [line for line in self.log if line.startswith(keyword)]
    if len(match) == 0:
      print("\nUnable to find", type, "average latency.")
      return -1
    
    line = match[0]
    idx1 = line.find('=')
    idx2 = line.find('(')
    latency = float(line[idx1+1:idx2])
    return latency


if __name__ == "__main__":
    stats_filename = "stats_out/out"
    FlitPathTable = Flit_path_table(n=2, k=4, filename=stats_filename)
    flit_path_map = FlitPathTable.flit_path_map
    print("flit path map: ")
    print(flit_path_map, "\n")
    uni_paths = FlitPathTable.extract_unique_path()
    print("find unique paths: ")
    print(uni_paths, "\n")

    log_filename = "log/fattree_configt1p70u.log"
    LogData = Booksim_log(log_filename)
    flit_latency = LogData.get_average_latency("Flit")
    print("Flit average latency: ", flit_latency, "\n")