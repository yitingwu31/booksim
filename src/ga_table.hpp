#include <list>
#include <map>
#include <set>
#include <cassert>
#include <vector>


class GATable {
    private: 
        std::map<std::pair<int,int>, std::vector<int> > _table;
    
    public:
        GATable();
        GATable(const std::string & filename);

        int find_next_node(int curr, int src, int dest);
        std::vector<int> get_path(int src, int dest);
};