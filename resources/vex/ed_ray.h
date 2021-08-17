
#ifndef ED_RAY
#define ED_RAY

#include "ed_vector.h"


struct Ray {
    vector pos; // ray position
    vector dir; // ray direction
    vector colour; // accumulated colour
    int vtx; // ray vertex to append next primitive
};

struct RayHit {
    vector colour;
    vector pos;
    int prim;
}

function vector sampleloomfield(
    int fieldgeo; vector pos){

    }

function float samplewell(
    vector pos; vector wellpos;
    float minrad, maxrad;
    float power, weight;
){
    // literally just fancy mapping of straight line distance
    // normalised depth of ray in field range
    vector d = wellpos - pos;
    float u = (length(d) - minrad) / (maxrad - minrad);

    float radsquare = pow( u, power );
    float wellweight = weight / radsquare;
    return wellweight;
}


function int[] trace(vector pos; vector dir; vector endpos; vector enddir;
    int indomain;
    string indomains[];
    float steplen, maxlen;
    int collision_geo; int loom_geo;
    int debugprim;
){
    /* trace a single timestep of this ray
    expects polyline primitives, each with a Ray
    struct as a prim attribute

    returns -1 until ray hits something,
    */
    vector hitpos, uvw;
    // change step length if ray is within loom
    if(indomain < 1){
        dir = normalize(dir) * maxlen;
    }
    else{
        dir = normalize(dir) * steplen;
    }
    int hitprim = intersect(collision_geo, pos, dir, hitpos, uvw);
    endpos = hitpos;
    enddir = dir;

    if(hitprim > -1){

        hitpos = hitpos - normalize(dir) * EPS;
        endpos = hitpos;
        vector hitN = prim(collision_geo, "N", hitprim);

        // check if hit prim is a loom domain
        if(prim(collision_geo, "loom_domain", hitprim)){
            string fieldid = prim(collision_geo, "loom_domainid", hitprim);
            // check normals, loom domains are boolean combined
            if (dot(dir, hitN) > 0){ // ray escapes volume
                indomain = indomain - 1;
                removevalue(indomains, fieldid);
                endpos = hitpos + hitN * EPS; // push out along normal
                enddir = dir;
            }
            else{ // ray enters volume
                indomain = indomain + 1;
                append(indomains, fieldid);
                endpos = hitpos - hitN * EPS; // pull in along normal
                enddir = dir;
            }
        }
        else{

            // hits normal piece of geometry
            enddir = reflect(normalize(dir), normalize(hitN));
            endpos = hitpos + EPS * enddir;
            indomain = indomain;
        }

        }
    else{ // no hit
        if(indomain){
            // sample loom field curvature
            // sum wells forces, very simple for now
            float weightsum = 0.0;
            vector gradsum = {0, 0, 0};

            // get sample points for scalar field
            vector tetpoints[], tetweights[];
            tetdirs(pos, tetpoints);

            foreach(string fieldid; indomains){

                // filter relevant geo
                int pts[] = expandpointgroup(
                    collision_geo, "@loom_domainid==" + fieldid);
                int pt = pts[0];

                // extract params
                vector wellpos = point(loom_geo, "P", pt);
                float power = point(loom_geo, "loom_power", pt);
                float weight = point(loom_geo, "loom_weight", pt);
                float minrad = point(loom_geo, "loom_minrad", pt);
                float maxrad = point(loom_geo, "loom_maxrad", pt);

                // sample scalar field at tet vertices
                float tetweightsum = 0.0;
                vector tetsum = {0, 0, 0};

                foreach(vector tetdir; tetpoints){
                    float fieldval = samplewell(
                        pos + tetdir * EPS, wellpos,
                        minrad, maxrad,
                        power, weight );
                    weightsum += fieldval;
                    vector tetvertval = tetdir * fieldval;
                    tetsum += tetvertval;
                }
                weightsum += tetweightsum;
                gradsum += tetsum;
            }
            vector graddir = gradsum;
            enddir = normalize(dir + graddir) * steplen;
            endpos = pos + enddir;

        }
        else{ // just normal tracing
            endpos = pos + dir;
            enddir = dir;
        }
    }
    return array(hitprim, indomain);

}




#endif
