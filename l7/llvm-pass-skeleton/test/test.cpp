#include <iostream>
#include <fstream>
#include <cstdlib>
#include <ctime>
#include <chrono>

std::string filename = "output.txt";
int iterations = 1e10;
int max_power = 10;

int main(int argc, char* argv[]) {
    if (argc > 1) filename = argv[1];              
    if (argc > 2) iterations = std::stoi(argv[2]); 
    if (argc > 3) max_power = std::stoi(argv[3]);

    std::srand(42); // seeded rng

    std::ofstream outFile(filename);
    if (!outFile) {
        std::cerr << "Error opening output file: " << filename << "\n";
        return 1;
    }

    auto start_time = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < iterations; ++i) {
        int op1 = std::rand() % 10001;
        int op2 = 1 << (std::rand() % (max_power + 1));

        if (std::rand() & 1) { // choose mul or div
            if (std::rand() & 1) { // swap mul args
                std::swap(op1, op2);
            }
            int result = op1 * op2;
            outFile << op1 << " * " << op2 << " = " << result << "\n";
        } else {
            if (std::rand() & 1) { // signed or unsigned division
            outFile << static_cast<unsigned int>(op1) << " /u " 
                    << static_cast<unsigned int>(op2) << " = " 
                    << (static_cast<unsigned int>(op1) / static_cast<unsigned int>(op2)) 
                    << "\n";
            } else {
            outFile << op1 << " / " << op2 << " = " << (op1 / op2) << "\n";
            }
        }
    }

    // End timing
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_time = end_time - start_time;

    outFile << "Elapsed time: " << elapsed_time.count() << " seconds\n";
    outFile.close();

    std::cout << "Elapsed time: " << elapsed_time.count() << " seconds" << std::endl;
    std::cout << "Results written to " << filename << std::endl;

    return 0;
}
