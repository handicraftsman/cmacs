#pragma once

#include <iostream>

namespace Example {

//using namespace foo;
// Here goes code which will be available to both header and implementation(s)

class Main {
public:
// Note that you cannot omit names of cpp-used namespaces in argument declarations and other header-side code snippets
Main(int foo, int bar, const std::string& baz)
: foo_(foo)
, bar_(bar)
, baz_(baz)
{
// This is available in implementations
cout << "Hello, World!" << endl;
}
int foo_plus_bar ();
static int main (int argc, char** argv);
private:
int foo_;
int bar_;
std::string baz_;
};
}
