
/*
testing basic principles behind loom field / spatial distortion
and light transport here in vex,
before likely herculaean task of porting to maya

first case: basic mirror sphere.

going fully naive for now, but consider the glancing angle case -
on a mirror skein, may take view ray many bounces to escape -
is there a way to precache entry and exit view vectors for a given camera
position?

consider keeping track of previous positions, doing manhattan distance check
on each bounce - if ray ends up bouncing between 2 spots, stop?

lighting is entirely decoupled from rendering - trace out from lights first,
store result as primitive attributes

*/


struct Ray {
    vector pos;
    vector dir;
    float time;
    vector colour;
    int vtx;
};

struct RayHit {
    vector colour;
    vector pos;
};

function void castlightray(Ray ray; int fieldgeo; int maxbounces;
    float bias; float decay;
    int debug){
    /* cast out ray until it hits geometry
    */
    // bounding box for collision geo
    vector bbmin, bbmax;
    getbbox( fieldgeo, bbmin, bbmax );
    float maxlen = length(bbmin - bbmax);

    for(int i = 0; i < maxbounces; i++){
        // raycast
        vector uvw, hitpos;
        int hitprim = intersect(0, ray.pos, ray.dir * maxlen, hitpos, uvw);

        if(debug){ // add lines to see where light is bouncing
            int oldvtx = ray.vtx;

            ray.vtx = addpoint(0, hitpos);
            setpointattrib(0, "Cd", ray.vtx, ray.colour);
            addprim(0, "polyline", oldvtx, ray.vtx);
        }

        if( prim(0, "field", hitprim) == 0){
            // hit on collision geo
            vector baseIrr = prim(0, "irradiance", hitprim);
            baseIrr += ray.colour;
            setprimattrib(0, "irradiance", hitprim, baseIrr);
            break;
        }
        vector normal = primuv(0, "N", hitprim, uvw);
        ray.dir = reflect(ray.dir, normal);
        ray.pos = hitpos + ray.dir * bias;
        ray.colour *= decay;

    }


}


function RayHit castprimaryray(vector pos; vector dir; vector eyedir;
    int collidegeo){
    /* called to cast out primary rays from visible loom skein,
    not to the */
    RayHit result;
    Ray ray;
    ray.pos = pos; ray.dir = dir;

    // bounding box for collision geo
    vector bbmin, bbmax;
    getbbox( collidegeo, bbmin, bbmax );
    float maxlen = length(bbmin - bbmax);


    // raycast
    vector uvw, hitpos;
    int hitprim = intersect(collidegeo, pos, dir * maxlen, hitpos, uvw);
    result.pos = hitpos;

    // check if another loom skein is hit
    int hitField = prim(collidegeo, "field", hitprim);
    if ( hitField > 0){
        // another field surface has been hit
        result.colour = set(1, 1, 1);
        return result;
    }

    if (hitprim < 0){
        result.colour = set(0, 0, 0);
        return result;
    }

    //interpolate values at point
    result.colour = primuv(collidegeo, "Cd", hitprim, uvw);


    return result;
}
