#include "example.cm.cpp.hpp"
using namespace Example;

using namespace std;

Main::Main(int foo, int bar, const std::string &baz) : foo_(foo), bar_(bar) {
  // This is available in implementations
  cout << "Hello, World!" << endl;
}
Main::~Main() {
  // some code
}
int Main::foo_plus_bar() { return foo_ + bar_; }
int Main::main(int argc, char **argv) {
  cout << Main(1, 2, "asdf").foo_plus_bar() << endl;
  return 0;
}
int main(int argc, char **argv) { return ::Example::Main::main(argc, argv); }