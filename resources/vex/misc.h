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


// fraction wrangle
// place after meta import in for loop
float fraction = 1.0 / (@numiterations - 1)
    * @iteration;
f@fraction = fraction;


// extract params from folders within loop
string node = chs("paramNode");
string attrs[] = {
    "width",
    "strands"
    }; // attrs in folders to extract

foreach( string at; attrs){
    string newname = sprintf( at+"%f", i@iteration + 1 );
    string param = node + newname;
    float val = ch(param);
    setdetailattrib(0, at, val);
    }

/*
consider "loopParams" hda
provide fraction and above map of attribute values on this iteration
as direct parms, given folder attribute to loop over


*/
