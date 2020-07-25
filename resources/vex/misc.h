// a place to put common wrangles that don't fit functions

// displace points along vector by ramp
vector dir = chv("direction");
float strength = chf("strength");

float fraction = 1.0 / (npoints(0) - 1 ) * @ptnum;

v@P = v@P + dir * strength * chramp("profile", fraction);


// group ends of curve
string name = "ends";
int n = neighbourcount(0, @ptnum);
if (n == 1) { setpointgroup(0, name, @ptnum, 1);}
