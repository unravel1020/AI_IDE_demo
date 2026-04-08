#include <iostream>
using namespace std;

class Base {
public:
    virtual void func() { cout << "Base" << endl; }
};

class Derived : public Base {
public:
    void func() { cout << "Derived" << endl; }
};

int main() {
    Base* p = new Derived();
    delete p;
    return 0;
}