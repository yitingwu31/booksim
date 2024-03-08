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
        yid = int(mid_fullname.split("_")[1])
        xid = int(mid_fullname.split("_")[2])
        mid = yid * self.k + xid
        self.flit_path_map[flit_id].append(mid)

  def extract_unique_path(self):
    paths = self.flit_path_map.values()
    unipaths = set(tuple(i) for i in paths)
    return unipaths

  


if __name__ == "__main__":
    filename = "stats_out/out"
    FlitPathTable = Flit_path_table(n=2, k=2, filename=filename)
    flit_path_map = FlitPathTable.flit_path_map
    print("flit path map: ")
    print(flit_path_map, "\n")
    uni_paths = FlitPathTable.extract_unique_path()
    print("find unique paths: ")
    print(uni_paths)