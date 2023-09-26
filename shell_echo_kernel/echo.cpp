#include <iostream>
#include <fstream>
#include <string>
using namespace std;

inline bool ends_with(std::string const & value, std::string const & ending)
{
    if (ending.size() > value.size()) return false;
    return std::equal(ending.rbegin(), ending.rend(), value.rbegin());
}

int main() {
    string to_out = "";
    string prompt = "clang-repl> ";
    string prompt_cont = "clang-repl... ";
    cout << prompt;
    for (string line; getline(std::cin, line);) {
        if (ends_with(line, "\\")) {
            line.pop_back();
            to_out+=line + "\n";
            cout << prompt_cont;
        } else {
            to_out+=line + "\n";
            cout << to_out;
            cout << prompt ;
            to_out = "";
        }

    }
    return 0;
}