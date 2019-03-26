#include "example.cm.cpp.hpp"
using namespace Example;

using namespace std;

int Main::foo_plus_bar () {
    return foo_ + bar_;
  }
int Main::main (int argc, char** argv) {
    cout << foo_plus_bar() << endl;
  }
int ::main(int argc, char** argv) { return ::Main::main(argc, argv); }