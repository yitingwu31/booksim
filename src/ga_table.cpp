#include "ga_table.hpp"

GATable::GATable() {
    // _table = ...
}

int GATable::find_next_node( int cur, int src, int dest)
{
    std::vector<int> target_path = get_path(src, dest);

    int next_node = -1;
    for (auto it=target_path.begin(); it!=target_path.end(); ++it) {
        if (*it == cur) {
            next_node = *(++it);
            break;
        }
    }

    return next_node;
}

std::vector<int> GATable::get_path(int src, int dest) {
    // Find next node from LUT using (src, dest)
    std::pair<int,int> key = std::make_pair(src, dest);
    std::vector<int> target_path = _table[key];
}