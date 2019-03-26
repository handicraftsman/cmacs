#pragma cmacs includes
{
  #include <iostream>
}

#pragma cmacs namespace Example

#pragma cmacs nop "Just a string example"

#pragma cmacs hpp
{
  //using namespace foo;
  // Here goes code which will be available to both header and implementation(s)
}

#pragma cmacs cpp
{
  using namespace std;
}

#pragma cmacs class
class Main {
public:
  // Note that you cannot omit names of cpp-used namespaces in argument declarations and other header-side code snippets
  #pragma cmacs constructor
  Main(int foo, int bar, const std::string& baz)
  : foo_(foo)
  , bar_(bar)
  , baz_(baz)
  {
    // This is available in implementations
    cout << "Hello, World!" << endl;
  }

  #pragma cmacs destructor
  virtual ~Main() {
    // some code
  }

  #pragma cmacs method
  int foo_plus_bar() {
    return foo_ + bar_;
  }

  #pragma cmacs main
  int main(int argc, char** argv) {
    cout << Main(1, 2, "asdf").foo_plus_bar() << endl;
    return 0;
  }

private:
  int foo_;
  int bar_;
  std::string baz_;
};