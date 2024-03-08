#include "ga_table.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
using namespace std;

template <typename S>
ostream& operator<<(ostream& os,
                    const vector<S>& vector)
{
    for (auto element : vector) {
        os << element << " ";
    }
    return os;
}

GATable::GATable() {
    // cout << "calling GA Table constructor" << endl;
    std::vector<int> path_0_to_1, path_0_to_2, path_0_to_3, 
                     path_1_to_0, path_1_to_2, path_1_to_3, 
                     path_2_to_1, path_2_to_0, path_2_to_3, 
                     path_3_to_1, path_3_to_2, path_3_to_0;

    path_0_to_1.push_back(0); path_0_to_1.push_back(1);
    path_0_to_2.push_back(0); path_0_to_2.push_back(2); 
    path_0_to_3.push_back(0); path_0_to_3.push_back(1); path_0_to_3.push_back(3);

    path_1_to_0.push_back(1); path_1_to_0.push_back(0);
    path_1_to_2.push_back(1); path_1_to_2.push_back(0); path_1_to_2.push_back(2);
    path_1_to_3.push_back(1); path_1_to_3.push_back(3);

    path_2_to_1.push_back(2); path_2_to_1.push_back(3); path_2_to_1.push_back(1);
    path_2_to_0.push_back(2); path_2_to_0.push_back(3); path_2_to_0.push_back(1); path_2_to_0.push_back(0);
    path_2_to_3.push_back(2); path_2_to_3.push_back(3);

    path_3_to_1.push_back(3); path_3_to_1.push_back(2); path_3_to_1.push_back(0);  path_3_to_1.push_back(1);
    path_3_to_2.push_back(3); path_3_to_2.push_back(2);
    path_3_to_0.push_back(3); path_3_to_0.push_back(1); path_3_to_0.push_back(0);

    
    _table[std::make_pair(0, 1)] = path_0_to_1;
    _table[std::make_pair(0, 2)] = path_0_to_2;
    _table[std::make_pair(0, 3)] = path_0_to_3;
    _table[std::make_pair(1, 0)] = path_1_to_0;
    _table[std::make_pair(1, 2)] = path_1_to_2;
    // cout << path_1_to_2 << endl;
    _table[std::make_pair(1, 3)] = path_1_to_3;
    _table[std::make_pair(2, 1)] = path_2_to_1;
    _table[std::make_pair(2, 0)] = path_2_to_0;
    _table[std::make_pair(2, 3)] = path_2_to_3;
    _table[std::make_pair(3, 1)] = path_3_to_1;
    _table[std::make_pair(3, 2)] = path_3_to_2;
    _table[std::make_pair(3, 0)] = path_3_to_0;
}


GATable::GATable(const std::string & path_filename) {
    ifstream path_list;
    path_list.open(path_filename.c_str());

    string line;
    if (path_list.is_open()) {
        while (!path_list.eof()) {
            getline(path_list, line);

            int start = line.find('(');
            int end = line.find(')');
            line = line.substr(start+1, end);

            if (line != "") {
                vector<int> nodes;
                stringstream ss(line);
                while (ss.good()) {
                    string substr;
                    getline(ss, substr, ',');
                    nodes.push_back(stoi(substr));
                }
                _table[std::make_pair(nodes[0], nodes[-1])] = nodes;
            }
        }
    }
}

int GATable::find_next_node( int cur, int src, int dest)
{
    // cout << "------ call find next node " << endl;
    std::vector<int> target_path = get_path(src, dest);
    // cout << "target path: " << target_path << endl;
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
    // cout << "------ call get path " << endl;
    std::pair<int,int> key = std::make_pair(src, dest);
    // cout << "key: (" << key.first << ", " << key.second << ")" << endl; 
    std::vector<int> target_path = _table[key];
    
    return target_path;
}


