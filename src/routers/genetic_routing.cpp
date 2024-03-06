#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random>


// Tournament selection
std::vector<int> selection(const std::vector<std::vector<int>>& pop, const std::vector<double>& scores, int k = 3) {
    int selection_ix = randint(0, pop.size());
    for (int i = 0; i < k - 1; ++i) {
        int ix = randint(0, pop.size());
        if (scores[ix] < scores[selection_ix]) {
            selection_ix = ix;
        }
    }
    return pop[selection_ix];
}

// Crossover two parents to create two children
std::vector<std::vector<int>> crossover(const std::vector<int>& p1, const std::vector<int>& p2, double r_cross) {
    std::vector<int> c1 = p1, c2 = p2;
    if (rand() < r_cross) {
        int pt = randint(1, p1.size() - 2);
        std::copy(p2.begin() + pt, p2.end(), c1.begin() + pt);
        std::copy(p1.begin() + pt, p1.end(), c2.begin() + pt);
    }
    return {c1, c2};
}

// Mutation operator
void mutation(std::vector<int>& bitstring, double r_mut) {
    for (size_t i = 0; i < bitstring.size(); ++i) {
        if (rand() < r_mut) {
            bitstring[i] = 1 - bitstring[i];
        }
    }
}


std::pair<std::vector<int>, double> genetic_algorithm(std::function<double(const std::vector<double>&)> objective,
                                                      const std::vector<std::pair<double, double>>& bounds,
                                                      int n_bits, int n_iter, int n_chrom, double r_cross, double r_mut) {
    std::vector<std::vector<int>> pop;
    for (int i = 0; i < n_chrom; ++i) {
        std::vector<int> bitstring(n_bits * bounds.size());
        std::generate(bitstring.begin(), bitstring.end(), []() { return randint(0, 2); });
        pop.push_back(bitstring);
    }

    std::vector<int> best = pop[0];
    double best_eval = objective(decode(bounds, n_bits, best));

    for (int gen = 0; gen < n_iter; ++gen) {
        std::vector<std::vector<double>> decoded;
        for (const auto& p : pop) {
            decoded.push_back(decode(bounds, n_bits, p));
        }

        std::vector<double> scores;
        std::transform(decoded.begin(), decoded.end(), std::back_inserter(scores), objective);

        for (int i = 0; i < n_chrom; ++i) {
            if (scores[i] < best_eval) {
                best = pop[i];
                best_eval = scores[i];
                std::cout << ">" << gen << ", new best f(" << decoded[i][0] << ", " << decoded[i][1] << ") = " << scores[i] << std::endl;
            }
        }

        std::vector<std::vector<int>> selected;
        for (int i = 0; i < n_chrom; ++i) {
            selected.push_back(selection(pop, scores));
        }

        std::vector<std::vector<int>> children;
        for (int i = 0; i < n_chrom; i += 2) {
            auto offspring = crossover(selected[i], selected[i + 1], r_cross);
            for (auto& child : offspring) {
                mutation(child, r_mut);
                children.push_back(child);
            }
        }
        pop = children;
    }
    return {best, best_eval};
}

int main() {
    std::vector<std::pair<double, double>> bounds = {{-5.0, 5.0}, {-5.0, 5.0}};
    int n = 2;
    int k = 4;
    int PATHS_MAX = (k^n)*k^(n-1);
    int n_iter = 100;
    int n_bits = 16;
    int n_chrom = 100;  // number of chromosomes in population
    double r_cross = 0.9;
    double r_mut = 1.0 / (n_bits * bounds.size());

    auto [best, score] = genetic_algorithm(fitness, bounds, n_bits, n_iter, n_chrom, r_cross, r_mut);
    auto decoded = decode(bounds, n_bits, best);
    
    std::cout << "Done!\n";
    std::cout << "f(" << decoded[0] << ", " << decoded[1] << ") = " << score << std::endl;

    return 0;
}