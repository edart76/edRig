
// testing preprocessor stuff

#define type int
type a = 1;
    // works, simple replacement
#define type string
type b = "b"
// macro redeclaration is sadly not possible
