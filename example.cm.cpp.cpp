#include "example.cm.cpp.hpp"
using namespace Example;

using namespace std;

Main::Main (int foo, int bar, const std::string& baz)
: foo_(foo)
, bar_(bar)
{
    // This is available in implementations
    cout << "Hello, World!" << endl;
  }
int Main::foo_plus_bar () {
    return foo_ + bar_;
  }
int Main::main (int argc, char** argv) {
    cout << foo_plus_bar() << endl;
  }
int ::main(int argc, char** argv) { return ::Main::main(argc, argv); }