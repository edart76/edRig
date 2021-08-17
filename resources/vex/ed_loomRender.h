
/*

loom attrs:
loom_maxrad - max distance at which loom effects activate
loom_minrad - minimum distance, loom effects at maximum
loom_weight - relative strength of this field component
loom_power - power falloff of field strength

loom_map - primitive number to map to. for now has to be merged

loom_domainid - prim and point flag used for geometry representing maximum distance
    of loom effect - if ray collides with this, begin loom processing.
    id corresponds to field's index

loom_type - preprocessor enum int flag for different types of loom fields

loom_wells - point group on loom geo input (2) -
    denotes point wells


ray attrs:
loom_indomain - ray flag saying how many layers deep ray is in loom fields
loom_indomains - indices of fields affecting ray
ray_dead - increments with each max-distance iteration
    without collision - after cutoff rays are ignored



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
#include "ed_ray.h"



function int castlightray(Ray ray; int fieldgeo; int maxbounces;
    float bias; float decay;
    int debug; int outputpoint){
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
            if(outputpoint){
                // output new point with irradiance info
                int newpt = addpoint(0, hitpos);
                setpointattrib(0, "irradiance", newpt, ray.colour);
                setpointgroup(0, "lightpoints", newpt, 1);
                return newpt;
            }
            else{
                // add irradiance to hit primitive
                vector baseIrr = prim(0, "irradiance", hitprim);
                baseIrr += ray.colour;
                setprimattrib(0, "irradiance", hitprim, baseIrr);
                break;
            }
        }
        else{
            // hit on field geo
            vector normal = primuv(0, "N", hitprim, uvw);
            ray.dir = reflect(ray.dir, normal);
            ray.pos = hitpos + ray.dir * bias;
            ray.colour *= decay;
        }

    }
    return -1;


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
